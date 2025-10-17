import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # src/sdlg_edu から見て親=src
import argparse, os, json, re, random
from typing import List, Dict
import re
from sdlg_edu.text_utils import de_template_explanation

# === Auto-injected: lightweight paraphrase helpers to reduce 5-gram collisions ===
try:
    _PARA_HELPERS_READY  # sentinel
except NameError:
    _PARA_HELPERS_READY = True

PARA_EN = [
    (r"\bpresent result/state\b", ["a current outcome", "present relevance"]),
    (r"\bfinished past event\b", ["a completed past action", "a past occurrence"]),
    (r"\bwith no present relevance\b", ["that does not affect the present", "with no current link"]),
    (r"\bwhereas\b", ["while", "in contrast"]),

    (r"\bChoose the correct article\b", ["Select the appropriate article", "Decide which article fits"]),
    (r"\bFill in the blank\b", ["Complete the blank", "Insert the missing word"]),
    (r"\bAnswer:\b", ["Solution:", "Response:"]),
]

def _paraphrase_en(r, s: str) -> str:
    """Light paraphrase only (conservative)."""
    if not isinstance(s, str) or not s:
        return s
    # 短文は触らない（極端な収束を防ぐ）
    if len(s) < 40:
        return s
    for pat, choices in PARA_EN:
        if r.random() < 0.45:  # ←控えめ
            s = re.sub(pat, r.choice(choices), s)
    return s

WORD_RE = re.compile(r"[A-Za-z']+")

COLUMNS = ["id","topic","question_en","answer_en","explanation_ja","difficulty","source"]

# 変化用の小さな語彙プール（決定論的：random.Random(seed) を使用）
NAMES = ["Alice","Ben","Chloe","David","Emma","Felix","Grace","Hiro","Ivy","Ken"]
PLACES = ["Paris","Berlin","Kyoto","New York","Osaka","London","Seoul","Sydney","Toronto","Rome"]
TIME_PHRASES = ["yesterday","last year","last week","in 2019","two days ago","this morning","on Monday"]
OBJECTS = ["my homework","the report","dinner","a new book","his leg","the car","the movie","the project","the keys"]

# 不規則動詞（base, past, past_participle）
VERBS = [
    ("go","went","gone"),
    ("see","saw","seen"),
    ("take","took","taken"),
    ("break","broke","broken"),
    ("write","wrote","written"),
    ("eat","ate","eaten"),
    ("buy","bought","bought"),
    ("finish","finished","finished"),
    ("live","lived","lived")
]

EXPLAIN_PP_VS_PAST_JA = [
    "現在完了は現在への結果や継続・経験を示し、過去形は完了した出来事を述べる。",
    "現在完了は“今につながる”点を強調し、過去形は“その時点で完了”を述べる。",
    "現在完了は結果・経験・継続のいずれかで現在への影響がある。過去形は時点を切り離す。",
    "現在完了は現在との関連、過去形は単に過去の事実を述べる。"
]

EXPLAIN_ARTICLES_JA = [
    "a/an は新情報の単数名詞、the は特定化、無冠詞は総称・複数・不可算など。",
    "母音音は an、子音音は a、特定なら the、一般なら無冠詞。",
    "冠詞は可算/不可算・特定/非特定で使い分ける（a/an, the, 無冠詞）。"
]


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

INSTR_PP = [
    "Explain the difference between '{A}' and '{B}'.",
    "How does '{A}' differ from '{B}'?",
    "Contrast '{A}' with '{B}'.",
    "In what situations would you use '{A}' rather than '{B}'?",
    "When is '{A}' appropriate, and when is '{B}' better?",
    "Compare '{A}' and '{B}' in terms of meaning and use.",
    "Rewrite and explain: '{A}' vs '{B}'.",
    "Give a brief contrast between '{A}' and '{B}'."
]

ANS_PP = [
    "{A} highlights a present result/state, whereas {B} reports a finished past event.",
    "Use {A} for present relevance; use {B} for a completed event at a known time.",
    "{A} connects to now; {B} is detached in time.",
    "{A} implies current impact, while {B} simply states a past fact.",
    "Prefer {A} when the present matters; prefer {B} for a past moment.",
    "{A} = present relevance. {B} = past event with no current link."
]

ADVERBS = ["already","just","recently","ever","never","yet","so far"]
CONNECT = ["whereas","while","however","but","in contrast"]

NAMES += ["Liam","Noah","Olivia","Mia","Yuki","Sora","Akira"]
PLACES += ["Nagoya","Barcelona","Vancouver","Dublin","Bangkok","Lisbon","Jakarta"]
TIME_PHRASES += ["in 2020","this year","earlier today","over the weekend","on Friday night"]
OBJECTS += ["the prototype","the assignment","a presentation","the tickets","the apartment","the dataset"]
VERBS += [("build","built","built"),("design","designed","designed"),("lose","lost","lost"),("find","found","found")]




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
    name = r.choice(NAMES)
    place = r.choice(PLACES)
    base, past, ppart = r.choice(VERBS)
    obj = r.choice(OBJECTS)
    when = r.choice(TIME_PHRASES)
    adv = r.choice(ADVERBS) if r.random() < 0.6 else None  # 6割で副詞注入
    use_contraction = (r.random() < 0.5)

    # 文の素体を作る
    if base == "go":
        sent_pp = f"{name} has {ppart} to {place}"
        sent_past = f"{name} {past} to {place} {when}"
    elif base == "live":
        sent_pp = f"{name} has {ppart} in {place} for ten years"
        sent_past = f"{name} {past} in {place} {when}"
    else:
        sent_pp = f"{name} has {ppart} {obj}"
        sent_past = f"{name} {past} {obj} {when}"

    # 副詞を挿入
    if adv and "has " in sent_pp:
        sent_pp = sent_pp.replace("has ", f"has {adv} ", 1)

    # 短縮形（She's / They've など）
    if use_contraction:
        sent_pp = sent_pp.replace(f"{name} has", f"{name}’s", 1)  # ’ は normalizeで'に統一される

    # 句読点を最後に付ける
    sent_pp += "."
    sent_past += "."

    # ときどき順序を逆転（過去→現在完了）
    if r.random() < 0.4:
        first, second = sent_past, sent_pp
    else:
        first, second = sent_pp, sent_past

    instr = r.choice(INSTR_PP)
    ans_tpl = r.choice(ANS_PP)
    conj = r.choice(CONNECT)

    # 質問と答え（接続詞のバリエーション）
    q = instr.format(A=first.rstrip("."), B=second.rstrip("."))
    a_en = ans_tpl.format(A=first, B=second)
    if r.random() < 0.5:
        a_en = a_en.replace(", whereas ", f", {conj} ")

    jp = r.choice(EXPLAIN_PP_VS_PAST_JA)

    return {
        "question_en": normalize_text(q),
        "answer_en": normalize_text(a_en),
        "explanation_ja": normalize_text(jp)
    }


def gen_articles(r: random.Random) -> Dict[str,str]:

    ART_INSTR = [
    "Choose the correct article: '{SENT}'",
    "Select the best article for the blank: '{SENT}'",
    "Fill in the blank with an appropriate article: '{SENT}'",
    "What article fits best here? '{SENT}'"
    ]

    # いくつかの空所文テンプレを回す
    patterns = [
        ("{lead} __ university near my house.", "There is", "a"),
        ("{lead} __ umbrella because it was raining.", "I bought", "an"),
        ("Please open __ door, not the window.", None, "the"),
        ("She is __ engineer and works at a startup.", None, "an"),
        ("We need __ information before we decide.", None, "(no article)"),
        ("He found __ old map in the attic.", None, "an"),
        ("They adopted __ cat from the shelter.", None, "a"),
        ("Close __ door, please.", None, "the"),
    ]
    lead_name = r.choice(NAMES)
    lead = r.choice([lead_name, "I", "We", "They", "She", "He"])

    sent_tpl, lead_phrase, ans = r.choice(patterns)
    sent = sent_tpl.format(lead=lead if lead_phrase is None else lead_phrase)

    instr = r.choice(ART_INSTR)
    tpl_a = "Correct: {ANS}" if r.random() < 0.5 else "Answer: {ANS}"
    jp = r.choice(EXPLAIN_ARTICLES_JA)
    q = instr.format(SENT=sent)
    a_en = tpl_a.format(ANS=ans)
    return {
        "question_en": normalize_text(q),
        "answer_en": normalize_text(a_en),
        "explanation_ja": normalize_text(jp)
    }

def gen_fallback(r: random.Random, topic: str) -> Dict[str,str]:
    tpl_q, tpl_a, tpl_jp = r.choice(TEMPLATES["_fallback"])
    sample_answer = f"A sample sentence about {topic}."
    return {
        "question_en": normalize_text(tpl_q.format(TOPIC=topic)),
        "answer_en": normalize_text(tpl_a.format(ANS=sample_answer)),
        "explanation_ja": normalize_text(tpl_jp)
    }

def build_item(r: random.Random, idx: int, topic: str, pattern: str) -> Dict[str, str]:
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

    # ★ ここで英語側のみ軽いパラフレーズを適用（決定論性は seed で担保）
    base["question_en"] = _paraphrase_en(r, base.get("question_en", ""))
    base["answer_en"]   = _paraphrase_en(r, base.get("answer_en", ""))

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

def get_ngrams(text: str, n: int = 5):
    toks = [t.lower() for t in WORD_RE.findall(text)]
    return [' '.join(toks[i:i+n]) for i in range(len(toks)-n+1)]

def build_with_dedup(r: random.Random, idx: int, spec: Dict[str,str], seen_ngrams: set,
                     max_trials: int = 36, max_overlap_ratio: float = 0.02):
    """
    既出5-gramとの重なりが max_overlap_ratio を超えたら再生成。
    成功時: (item, grams) を返す。失敗時: (None, set())。
    """
    last_item = None
    last_grams = set()
    for _ in range(max_trials):
        item = build_item(r, idx, spec["topic"], spec["pattern"])
        blob = (item.get("question_en","") + " " + item.get("answer_en","")).strip()
        grams = set(get_ngrams(blob, 5))
        if not grams:
            return item, set()
        overlap = len(grams & seen_ngrams) / max(1, len(grams))
        if overlap <= max_overlap_ratio:
            return item, grams
        last_item, last_grams = item, grams
    # どうしても下がらない場合は不採用にする（Noneを返す）
    return None, set()

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
    total_written = 0
    idx = 1
    seen_ngrams: set = set()
    with open(out_path, "w", encoding="utf-8") as wf:
        for spec in recipe:
            got = 0
            safety = 0
            # 各レシピ行ごとに所定数を満たすまで生成（上限 safety で無限ループ防止）
            while got < args.n_per_topic and safety < args.n_per_topic * 50:
                safety += 1
                item, grams = build_with_dedup(
                    r=r,
                    idx=idx,
                    spec=spec,
                    seen_ngrams=seen_ngrams,
                    max_trials=36,
                    max_overlap_ratio=0.02
                )
                if item is None:
                    continue  # dup過多 → 捨てて再試行
                # 正常時のみ書き込み
                wf.write(json.dumps(item, ensure_ascii=False) + "\n")
                seen_ngrams |= grams
                got += 1
                total_written += 1
                idx += 1

    print(f"Saved: {out_path}  ({total_written} rows)")
    print("Recipe lines:", len(recipe), "| per-topic:", args.n_per_topic)

if __name__ == "__main__":
    main()
