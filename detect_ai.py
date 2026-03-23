"""
Heuristic AI-generated comment detector for trekamdienstag.de comments.
Scores each comment on multiple signals and outputs ki_suspects.json.
"""

import json, re, sys
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class HTMLStripper(HTMLParser):
    def __init__(self): super().__init__(); self.fed = []
    def handle_data(self, d): self.fed.append(d)
    def get_data(self): return " ".join(self.fed).strip()

def strip_html(html):
    s = HTMLStripper(); s.feed(html); return s.get_data()

# ── Signal definitions ────────────────────────────────────────────────────────

# (explicit AI tool mentions removed — mentioning ChatGPT/KI is not a sign of AI-generated text)

# 2. Phrases that frequently appear in LLM output (DE + EN)
AI_PHRASES_DE = [
    r"insgesamt lässt sich (sagen|festhalten|feststellen)",
    r"zusammenfassend (lässt sich|kann man|ist zu)",
    r"es ist (wichtig|entscheidend|erwähnenswert) (zu beachten|anzumerken|hervorzuheben)",
    r"einerseits.*andererseits",
    r"zum einen.*zum anderen",
    r"abschließend (lässt sich|kann (man|ich))",
    r"es sei (darauf hingewiesen|angemerkt)",
    r"im großen und ganzen",
    r"auf den ersten blick.*jedoch",
    r"nichtsdestotrotz",
    r"in diesem zusammenhang",
    r"es bleibt (abzuwarten|festzuhalten|zu hoffen)",
    r"selbstverständlich",
    r"zweifelsohne",
    r"unbestreitbar",
    r"es versteht sich von selbst",
    r"ich hoffe.*geholfen",
    r"falls (du|ihr|sie) (weitere|noch) fragen",
    r"ich stehe.*zur verfügung",
    r"bei weiteren fragen",
]
AI_PATTERNS = [re.compile(p, re.I | re.S) for p in AI_PHRASES_DE]

# 3. Structural signals
BULLET_LIST   = re.compile(r"^\s*[*\-•]\s+\w", re.M)
NUMBERED_LIST = re.compile(r"^\s*\d+[.)]\s+\w", re.M)
SECTION_HDR   = re.compile(r"^\s*#{1,3}\s+\w|^\s*\*{1,2}[A-ZÜÄÖ][^*]+\*{1,2}\s*$", re.M)

# 4. Suspiciously uniform sentence length (LLMs tend to write similar-length sentences)
def sentence_length_variance(text):
    sentences = re.split(r"[.!?]+", text)
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 2]
    if len(lengths) < 4:
        return 1000  # not enough data → not suspicious
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance

# 5. Transition word density (LLMs overuse connectors)
TRANSITIONS = re.compile(
    r"\b(jedoch|allerdings|dennoch|deshalb|daher|somit|folglich|infolgedessen"
    r"|zudem|überdies|darüber hinaus|nichtsdestoweniger|gleichwohl)\b",
    re.I
)

# ── Scoring ───────────────────────────────────────────────────────────────────

def score_comment(text_raw, text):
    signals = []
    score = 0

    # AI phrase patterns
    matched_phrases = [p.pattern for p in AI_PATTERNS if p.search(text)]
    if matched_phrases:
        pts = 15 * len(matched_phrases)
        score += pts
        signals.append(f"{len(matched_phrases)} AI phrase(s): {'; '.join(matched_phrases[:3])}")

    # Bullet/numbered lists (structured output)
    bullets = len(BULLET_LIST.findall(text))
    numbered = len(NUMBERED_LIST.findall(text))
    if bullets + numbered >= 3:
        score += 10 * (bullets + numbered)
        signals.append(f"Heavy list structure: {bullets} bullets, {numbered} numbered items")

    # Section headers
    hdrs = len(SECTION_HDR.findall(text))
    if hdrs >= 2:
        score += 15 * hdrs
        signals.append(f"{hdrs} section header(s)")

    # Length alone isn't suspicious, but very long + other signals amplify
    words = len(text.split())
    if words > 400:
        score += 5
        signals.append(f"Long comment ({words} words)")

    # Low sentence variance (uniform sentence length = LLM tell)
    variance = sentence_length_variance(text)
    if variance < 10 and len(text.split()) > 80:
        score += 20
        signals.append(f"Suspiciously uniform sentence length (variance={variance:.1f})")

    # Transition word density
    word_count = max(len(text.split()), 1)
    trans = len(TRANSITIONS.findall(text))
    density = trans / word_count
    if density > 0.04 and trans >= 3:
        score += int(density * 200)
        signals.append(f"High transition word density: {trans} transitions in {word_count} words ({density:.1%})")

    # HTML contains <ol> or <ul> tags (structured list in HTML source)
    if re.search(r"<(ul|ol)\b", text_raw, re.I):
        score += 20
        signals.append("HTML list tags present")

    return score, signals


# ── Main ──────────────────────────────────────────────────────────────────────

comments = json.loads(Path("comments/all_comments.json").read_text(encoding="utf-8"))

results = []
for c in comments:
    text = strip_html(c["content"])
    if len(text) < 30:
        continue
    score, signals = score_comment(c["content"], text)
    if score >= 20:
        results.append({
            "comment_id":  c["comment_id"],
            "post_id":     c["post_id"],
            "post_title":  c["post_title"],
            "post_date":   c["post_date"],
            "post_slug":   c["post_slug"],
            "date":        c["date"],
            "author_name": c["author_name"],
            "score":       score,
            "signals":     signals,
            "text":        text[:600],
            "content_html": c["content"],
        })

results.sort(key=lambda x: x["score"], reverse=True)

Path("comments/ki_suspects.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)

print(f"Total comments analysed: {len(comments)}")
print(f"Suspects (score ≥ 20):   {len(results)}")
print(f"\nTop 15:")
print(f"{'Score':>6}  {'Author':<30}  Signals")
print("-" * 80)
for r in results[:15]:
    print(f"{r['score']:>6}  {r['author_name']:<30}  {r['signals'][0][:50]}")
