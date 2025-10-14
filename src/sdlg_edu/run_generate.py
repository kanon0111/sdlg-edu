import argparse, os, json

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--recipe", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--deterministic", action="store_true")
    p.add_argument("--outdir", default="outputs")
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    out = os.path.join(args.outdir, "english_grammar_qa.jsonl")
    # ひとまずダミー1件
    with open(out, "w", encoding="utf-8") as f:
        f.write(json.dumps({"id":"GRAM-000001","topic":"present perfect","question_en":"Explain the difference between 'I have gone' and 'I went'.","answer_en":"'I have gone' emphasizes a present result; 'I went' states a past event without present relevance.","explanation_ja":"現在完了は現在への結果・影響。過去形は過去時点の事実。","difficulty":"MEDIUM","source":"synthetic/local"}, ensure_ascii=False) + "\n")
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()
