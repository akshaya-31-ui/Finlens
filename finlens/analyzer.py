import os, re, io, joblib, requests
from pypdf import PdfReader
from prompts import SYSTEM, STRATEGIES

_MODEL = None
def tone_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = joblib.load(os.path.join(os.path.dirname(__file__), "model", "tone_model.joblib"))
    return _MODEL

def extract_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((p.extract_text() or "") for p in reader.pages)

# ---------- figure extraction ----------
NUM = re.compile(r"\(?-?\$?\s?\d[\d,]*\.?\d*\)?")
def to_num(tok):
    neg = tok.strip().startswith("(") or "-" in tok
    v = re.sub(r"[^\d.]", "", tok)
    if not v or v == ".": return None
    return -float(v) if neg else float(v)

LABELS = {
 "revenue": r"^(total )?(net )?(revenues?|sales|net sales)\b",
 "gross_profit": r"^gross (profit|margin)\b",
 "operating_income": r"^(operating (income|profit)|income from operations)\b",
 "net_income": r"^(net (income|profit|earnings)|profit (for the (year|period)|after tax))\b",
 "total_assets": r"^total assets\b",
 "current_assets": r"^total current assets\b",
 "total_liabilities": r"^total liabilities\b(?! and)",
 "current_liabilities": r"^total current liabilities\b",
 "equity": r"^total (shareholders'?|stockholders'?) ?equity\b|^total equity\b",
 "total_debt": r"^total (debt|borrowings)\b",
 "operating_cash_flow": r"^(net )?cash (provided by|from|generated (from|by)) operating activities|^cash flow from operations",
}
NAMES = {"revenue": "Revenue", "gross_profit": "Gross profit", "operating_income": "Operating income",
         "net_income": "Net income", "total_assets": "Total assets", "current_assets": "Current assets",
         "total_liabilities": "Total liabilities", "current_liabilities": "Current liabilities",
         "equity": "Shareholders' equity", "total_debt": "Total debt", "operating_cash_flow": "Operating cash flow"}

def find_figures(text):
    out = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for key, pat in LABELS.items():
        rx = re.compile(pat, re.I)
        for i, ln in enumerate(lines):
            m = rx.search(ln)
            if not m: continue
            nums = [to_num(t) for t in NUM.findall(ln[m.end():])]
            nums = [n for n in nums if n is not None]
            if not nums:   # table cells on their own lines: read ahead
                for nxt in lines[i + 1:i + 6]:
                    if not re.fullmatch(r"\(?-?\$?\s?\d[\d,]*\.?\d*\)?%?", nxt): break
                    nums.append(to_num(nxt))
                nums = [n for n in nums if n is not None]
            if len(nums) >= 3 and abs(nums[0]) < 100 and float(nums[0]).is_integer():
                nums = nums[1:]            # drop a "Note" column
            if nums:
                out[key] = {"current": nums[0], "prior": nums[1] if len(nums) > 1 else None}
                break
    if "total_liabilities" not in out and "total_assets" in out and "equity" in out:
        a, e = out["total_assets"], out["equity"]
        out["total_liabilities"] = {"current": a["current"] - e["current"],
            "prior": (a["prior"] - e["prior"]) if a["prior"] is not None and e["prior"] is not None else None,
            "derived": True}
    return out

def unit_hint(text):
    m = re.search(r"in (thousands|millions|billions)|\((?:rs|inr|usd|\$)?\s*(?:in )?(thousands|millions|crores?|lakhs?)\)", text[:6000], re.I)
    return (m.group(1) or m.group(2)).lower() if m else None

def cur(f, k): return f.get(k, {}).get("current")
def pri(f, k): return f.get(k, {}).get("prior")
def div(a, b): return None if a is None or not b else a / b
def growth(f, k):
    c, p = cur(f, k), pri(f, k)
    return None if c is None or not p else (c - p) / abs(p)

def ratios(f):
    debt = cur(f, "total_debt") if cur(f, "total_debt") is not None else cur(f, "total_liabilities")
    R = []
    def add(label, val, kind, good, weak, note):
        if val is None: return
        if kind == "pct": shown = f"{val*100:.1f}%"
        else: shown = f"{val:.2f}"
        hi = val >= good if good > weak else val <= good
        lo = val <= weak if good > weak else val >= weak
        R.append({"label": label, "value": shown, "raw": val, "status": "good" if hi else "weak" if lo else "watch", "note": note})
    add("Revenue growth", growth(f, "revenue"), "pct", .08, 0, "Change in revenue versus the prior year")
    add("Net income growth", growth(f, "net_income"), "pct", .08, 0, "Change in net income versus the prior year")
    add("Gross margin", div(cur(f, "gross_profit"), cur(f, "revenue")), "pct", .35, .15, "Share of revenue left after direct costs")
    add("Operating margin", div(cur(f, "operating_income"), cur(f, "revenue")), "pct", .12, .04, "Profit from core operations per unit of revenue")
    add("Net margin", div(cur(f, "net_income"), cur(f, "revenue")), "pct", .08, .02, "Final profit per unit of revenue")
    add("Return on equity", div(cur(f, "net_income"), cur(f, "equity")), "pct", .12, .05, "Profit generated on shareholders' money")
    add("Return on assets", div(cur(f, "net_income"), cur(f, "total_assets")), "pct", .06, .02, "Profit generated on everything the company owns")
    add("Current ratio", div(cur(f, "current_assets"), cur(f, "current_liabilities")), "x", 1.5, 1.0, "Short-term assets available to cover short-term bills")
    add("Debt to equity", div(debt, cur(f, "equity")), "x", 1.0, 2.0, "Borrowing and liabilities relative to owners' funds")
    add("Cash flow to net income", div(cur(f, "operating_cash_flow"), cur(f, "net_income")), "x", 1.0, .6, "Whether reported profit is backed by real cash")
    return R

def health(R):
    if not R: return None
    pts = {"good": 1, "watch": .5, "weak": 0}
    score = round(100 * sum(pts[r["status"]] for r in R) / len(R))
    return {"score": score, "label": "Strong" if score >= 70 else "Mixed" if score >= 45 else "Under pressure",
            "based_on": len(R)}

# ---------- tone detection (ML model + keyword lexicon) ----------
RISK_W = {"loss","decline","declined","impairment","litigation","going concern","default","uncertain","uncertainty","adverse","downturn","deteriorat","covenant","breach","write-down","penalt","investigation","weakness","volatil","shortfall"}
GROW_W = {"record","growth","grew","increase","increased","improved","expansion","expanded","strong","higher","raised","gained","launched","dividend","robust","surpass"}
def lex(s):
    s = s.lower()
    return sum(w in s for w in GROW_W) - sum(w in s for w in RISK_W)

def tone_sentences(text, limit=6):
    paras, buf = [], []
    for ln in (l.strip() for l in text.splitlines()):
        if not ln or (len(ln) < 70 and not re.search(r"[.,;:]$", ln)):   # headings and table cells end a paragraph
            if buf: paras.append(" ".join(buf)); buf = []
        else: buf.append(ln)
    if buf: paras.append(" ".join(buf))
    sents = [x.strip() for p in paras for x in re.split(r"(?<=[.!?])\s+(?=[A-Z])", p) if 50 <= len(x.strip()) <= 320]
    sents = [s for s in sents if len(re.findall(r"\d", s)) < len(s) * .15]
    if not sents: return {"risk": [], "growth": []}
    probs = tone_model().predict_proba(sents); classes = list(tone_model().classes_)
    risk, grow = [], []
    for s, p in zip(sents, probs):
        pr, pg = p[classes.index("risk")], p[classes.index("growth")]
        l = lex(s)
        pr += .15 * max(-l, 0); pg += .15 * max(l, 0)
        if pr > .5 and pr > pg and l <= 0: risk.append((pr, s))
        elif pg > .5 and pg > pr and l >= 0: grow.append((pg, s))
    top = lambda L: [{"text": s, "confidence": round(min(c, .99), 2)} for c, s in sorted(L, reverse=True)[:limit]]
    return {"risk": top(risk), "growth": top(grow)}

def summary(f, R, tones, units):
    bits = []
    rg, ng = growth(f, "revenue"), growth(f, "net_income")
    if rg is not None: bits.append(f"Revenue {'rose' if rg >= 0 else 'fell'} {abs(rg)*100:.1f}% compared with the prior year.")
    if ng is not None: bits.append(f"Net income {'rose' if ng >= 0 else 'fell'} {abs(ng)*100:.1f}%.")
    weak = [r["label"].lower() for r in R if r["status"] == "weak"]
    good = [r["label"].lower() for r in R if r["status"] == "good"]
    if good: bits.append("Stronger areas: " + ", ".join(good[:3]) + ".")
    if weak: bits.append("Areas that need attention: " + ", ".join(weak[:3]) + ".")
    if tones["risk"]: bits.append(f"The narrative sections contain {len(tones['risk'])} passage(s) that read as risk disclosures.")
    return " ".join(bits) or "Not enough recognisable figures were found to write a summary."

# ---------- optional LLM layer ----------
def llm_enabled(): return bool(os.getenv("ANTHROPIC_API_KEY"))

def llm_analysis(text, strategy):
    prompt = STRATEGIES.get(strategy, STRATEGIES["zero_shot"])(text[:60000])
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=90,
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"), "max_tokens": 1200, "system": SYSTEM,
              "messages": [{"role": "user", "content": prompt}]})
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])

def analyze(data: bytes, strategy="zero_shot"):
    text = extract_text(data)
    if len(text.strip()) < 200:
        raise ValueError("No readable text found. This looks like a scanned PDF; upload a text-based report.")
    f = find_figures(text); R = ratios(f); tones = tone_sentences(text)
    units = unit_hint(text)
    out = {"units": units, "pages_chars": len(text),
           "figures": [{"key": k, "label": NAMES[k], "current": v["current"], "prior": v["prior"],
                        "change": growth(f, k), "derived": v.get("derived", False)} for k, v in f.items()],
           "ratios": R, "health": health(R), "tone": tones, "summary": summary(f, R, tones, units),
           "llm": None, "llm_error": None, "strategy": strategy}
    if llm_enabled():
        try: out["llm"] = llm_analysis(text, strategy)
        except Exception as e: out["llm_error"] = f"AI commentary unavailable: {e}"
    return out
