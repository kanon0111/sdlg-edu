import argparse, os, json, re, random
from typing import List, Dict

COLUMNS = ["id","topic","question_en","answer_en","explanation_ja","difficulty","source"]

TEMPLATES = {
    "contrast_present_perfect_vs_past": [
        (
            "Explain the difference between '{A}' and '{B}'.",
            "'{A}' highlights a present result/state; '{B}' reports a finished past event with no present relevance.",
            "現在完了は現在への結果・影響を示す。一方、過去形は過去の事実を述べる。"
        ),
        (
            "Rewrite with the present perfect if appropriate: '{SENT}'. Then contrast it with the past simple.",
            "Present perfect: {A}. Past simple: {B}.",
            "現在完了は経験・継続・完了のうち、現在へのつながりを強調。過去形は時点を切り離す。"
        )
    ],
    "choose_correct_article": [
        (
            "Choose the correct article: '{SENT}'",
            "Correct: {ANS}",
            "可算名詞の単数は a/an。特定のものは the。無冠詞は複数や不可算の一般。"
        ),
        (
            "Fill in the blank with an article if needed: '{SENT}'",
            "Answer: {ANS}",
            "母音音から始まる語は an、子音音は a。特定化は the。不要なときは無冠詞。"
        )
    ],
    "_fallback": [
        (
            "Write one sentence using the topic: {TOPIC}.",
            "{ANS}",
            "トピックの用法を1文で自然に示す。"
        )
    ]
}

SENT_BANK = {
    "pp_vs_past": [
        ("I have already finished my homework.","I finished my homework yesterday."),
        ("She has gone to Paris.","She went to Paris in 2019."),
        ("They have lived here for ten years.","They lived here ten years ago."),
        ("He has broken his leg.","He broke his leg last year."),
    ],
    "articles": [
        ("__ a university near my house.", "There is"),
        ("I bought __ umbrella because it was raining.", "an"),
        ("Please open __ door, not the window.", "the"),
        ("She is __ engineer and works at a startup.", "an"),
        ("We need __ information before we decide.", "(no article)"),
    ]
}

def normalize_text(s: str) -> str:
    s = s.replace("’", "'").replace("“","\"").replace("”","\"")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def make_id(n: int) -> str:
    return f"GRAM-{n:06d}"

def pick_difficulty(r: random.Random) -> str:
    p = r.random()
    if p < 0.5: return "EASY"
    if p < 0.85: return "MEDIUM"
    return "HARD"

def gen_pp_vs_past(r: random.Random) -> Dict[str,str]:
    (a,b) = r.choice(SENT_BANK["pp_vs_past"])
    tpl_q, tpl_a, tpl_jp = r.choice(TEMPLATES["contrast_present_perfect_vs_past"])
    q = tpl_q.format(A=a.split(".")[0], B=b.split(".")[0], SENT=b)
    a_en = tpl_a.format(A=a, B=b)
    return {
        "question_en": normalize_text(q),
        "answer_en": normalize_text(a_en),
        "explanation_ja": normalize_text(tpl_jp)
    }

def gen_articles(r: random.Random) -> Dict[str,str]:
    sent, ans = r.choice(SENT_BANK["articles"])
    tpl_q, tpl_a, tpl_jp = r.choice(TEMPLATES["choose_correct_article"])
    q = tpl_q.format(SENT=sent)
    a_en = tpl_a.format(ANS=ans)
    return {
        "question_en": normalize_text(q),
        "answer_en": normalize_text(a_en),
        "explanation_ja": normalize_text(tpl_jp)
    }

def gen_fallback(r: random.Random, topic: str) -> Dict[str,str]:
    tpl_q, tpl_a, tpl_jp = r.choice(TEMPLATES["_fallback"])
    sample_answer = f"A sample sentence about {topic}."
    return {
        "question_en": normalize_text(tpl_q.format(TOPIC=topic)),
        "answer_en": normalize_text(tpl_a.format(ANS=sample_answer)),
        "explanation_ja": normalize_text(tpl_jp)
    }

def build_item(r: random.Random, idx: int, topic: str, pattern: str) -> Dict[str,str]:
    if pattern == "contrast_present_perfect_vs_past":
        base = gen_pp_vs_past(r)
    elif pattern == "choose_correct_article":
        base = gen_articles(r)
    else:
        base = gen_fallback(r, topic)

    base.update({
        "id": make_id(idx),
        "topic": topic,
        "difficulty": pick_difficulty(r),
        "source": "synthetic/local"
    })
    return base

def load_recipe(path: str) -> List[Dict[str,str]]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            obj = json.loads(line)
            topic = obj.get("topic","misc")
            pattern = obj.get("pattern","_fallback")
            items.append({"topic":topic, "pattern":pattern})
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--n-per-topic", type=int, default=50, help="Generate this many items for each recipe line")
    args = ap.parse_args()

    r = random.Random(args.seed)
    os.makedirs(args.outdir, exist_ok=True)
    out_path = os.path.join(args.outdir, "english_grammar_qa.jsonl")

    recipe = load_recipe(args.recipe)
    idx = 1
    with open(out_path, "w", encoding="utf-8") as wf:
        for spec in recipe:
            for _ in range(args.n_per_topic):
                item = build_item(r, idx, spec["topic"], spec["pattern"])
                wf.write(json.dumps(item, ensure_ascii=False) + "\n")
                idx += 1

    print(f"Saved: {out_path}  ({idx-1} rows)")
    print("Recipe lines:", len(recipe), "| per-topic:", args.n_per_topic)

if __name__ == "__main__":
    main()
