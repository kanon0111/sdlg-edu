import argparse, json, os, re
from collections import Counter

# -------------------------------
# Heuristics (no extra packages)
# -------------------------------

# ざっくり英語/日本語の判定
RE_LATIN = re.compile(r'[A-Za-z]')
RE_JP    = re.compile(r'[\u3040-\u30FF\u4E00-\u9FFF]')

# 簡易トキナイズ（英語想定）
WORD_RE = re.compile(r"[A-Za-z']+")

# 毒性ワードの超小規模辞書（必要に応じて拡張）
TOXIC_WORDS = {
    # mild safe-list; extend cautiously
    "hate", "stupid", "idiot"
}

# PII 検知の簡易版
RE_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
RE_PHONE = re.compile(r'(?:\+?\d[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}')
RE_ADDR_HINT = re.compile(r'\d{3}-\d{4}')  # 郵便番号っぽい

def read_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def has_english(s: str) -> bool:
    return bool(RE_LATIN.search(s))

def has_japanese(s: str) -> bool:
    return bool(RE_JP.search(s))

def language_ok(item) -> bool:
    # question/answer は英語、explanation は日本語を期待
    q_ok = has_english(item.get("question_en","")) and not has_japanese(item.get("question_en",""))
    a_ok = has_english(item.get("answer_en",""))   and not has_japanese(item.get("answer_en",""))
    e_ok = has_japanese(item.get("explanation_ja",""))
    return q_ok and a_ok and e_ok

def get_ngrams(text: str, n: int = 5):
    toks = [t.lower() for t in WORD_RE.findall(text)]
    return [' '.join(toks[i:i+n]) for i in range(len(toks)-n+1)]

def toxicity_hit(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in TOXIC_WORDS)

def pii_hit(text: str) -> bool:
    return bool(RE_EMAIL.search(text) or RE_PHONE.search(text) or RE_ADDR_HINT.search(text))

def summarize_quality(items):
    total = len(items)

    # language
    lang_ok = sum(1 for x in items if language_ok(x))
    language_match = (lang_ok / total) if total else 0.0

    # dup 5-gram
    all_ngrams = []
    for x in items:
        blob = ' '.join([
            x.get('question_en',''),
            x.get('answer_en',''),
            #x.get('explanation_ja',''),
        ])
        all_ngrams.extend(get_ngrams(blob, 5))
    dup_rate = 0.0
    if all_ngrams:
        c = Counter(all_ngrams)
        dup_count = sum(v-1 for v in c.values() if v > 1)
        dup_rate = dup_count / max(1, len(all_ngrams))

    # toxicity / pii
    tox_hits = 0
    pii_hits = 0
    for x in items:
        blob = ' '.join([x.get('question_en',''), x.get('answer_en',''), x.get('explanation_ja','')])
        if toxicity_hit(blob): tox_hits += 1
        if pii_hit(blob):      pii_hits += 1
    toxicity_rate = tox_hits / total if total else 0.0
    pii_rate      = pii_hits  / total if total else 0.0

    return {
        "count": total,
        "language_match": round(language_match, 4),
        "dup_5gram_rate": round(dup_rate, 4),
        "toxicity_rate":  round(toxicity_rate, 4),
        "pii_rate":       round(pii_rate, 4),
    }

def gate_pass(metrics):
    # RUN_MANIFEST.md の基準
    return (
        metrics["language_match"] >= 0.98 and
        metrics["dup_5gram_rate"] <= 0.02 and
        metrics["toxicity_rate"]  == 0.0 and
        metrics["pii_rate"]       == 0.0
    )

def write_markdown(path, m, passed):
    lines = []
    lines.append("# Quality Summary")
    lines.append("")
    lines.append(f"- items: **{m['count']}**")
    lines.append(f"- language_match: **{m['language_match']}** (>= 0.98)")
    lines.append(f"- dup_5gram_rate: **{m['dup_5gram_rate']}** (<= 0.02)")
    lines.append(f"- toxicity_rate: **{m['toxicity_rate']}** (= 0.00)")
    lines.append(f"- pii_rate: **{m['pii_rate']}** (= 0.00)")
    lines.append("")
    lines.append(f"**PASS:** {'✅' if passed else '❌'}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--out_md", required=True)
    args = ap.parse_args()

    items = list(read_jsonl(args.input))
    metrics = summarize_quality(items)
    passed = gate_pass(metrics)

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, 'w', encoding='utf-8') as f:
        json.dump({"metrics": metrics, "pass": passed}, f, ensure_ascii=False, indent=2)
    write_markdown(args.out_md, metrics, passed)

    print(json.dumps({"metrics": metrics, "pass": passed}, ensure_ascii=False))
    if not passed:
        # 失敗時は非0終了（パイプラインでFailにする想定）
        raise SystemExit(2)

if __name__ == "__main__":
    main()
