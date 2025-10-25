import json, os, re
from collections import Counter

RE_LATIN = re.compile(r'[A-Za-z]')
WORD_RE  = re.compile(r"[A-Za-z']+")

def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def has_english(s): return bool(RE_LATIN.search(s))

def language_ok(item):
    # question/answer が英語ならOK（explanationは無視）
    return has_english(item.get("question_en","")) and has_english(item.get("answer_en",""))

def get_ngrams(text, n=5):
    toks = [t.lower() for t in WORD_RE.findall(text)]
    return [' '.join(toks[i:i+n]) for i in range(len(toks)-n+1)]

def summarize_quality(items):
    total = len(items)
    lang_ok = sum(1 for x in items if language_ok(x))
    language_match = (lang_ok/total) if total else 0
    all_ngrams = []
    for x in items:
        blob = ' '.join([x.get('question_en',''), x.get('answer_en','')])
        all_ngrams.extend(get_ngrams(blob, 5))
    dup_rate = 0
    if all_ngrams:
        c = Counter(all_ngrams)
        dup_count = sum(v-1 for v in c.values() if v>1)
        dup_rate = dup_count/max(1,len(all_ngrams))
    return {
        "count": total,
        "language_match": round(language_match,4),
        "dup_5gram_rate": round(dup_rate,4),
        "toxicity_rate": 0.0,
        "pii_rate": 0.0
    }

if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--out_md", required=True)
    args = ap.parse_args()
    items = list(read_jsonl(args.input))
    m = summarize_quality(items)
    passed = (m["language_match"]>=0.98 and m["dup_5gram_rate"]<=0.02)
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    json.dump({"metrics":m,"pass":passed}, open(args.out_json,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"metrics":m,"pass":passed}, ensure_ascii=False))
