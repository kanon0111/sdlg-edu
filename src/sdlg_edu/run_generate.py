import argparse, json, random, re, os
from typing import Dict, Any, List

# ===== Pools (大幅拡張) =====
NAMES = ["Liam","Olivia","Noah","Emma","Ava","Mason","Sophia","Isabella","Ethan","Mia","Lucas","Amelia","Harper","James","Emily",
"David","Chloe","Henry","Ella","Jack","Grace","Leo","Aria","Benjamin","Aiden","Elijah","Scarlett","Daniel","Hannah","Jacob",
"Victoria","Samuel","Layla","Andrew","Zoey","Michael","Nora","Joseph","Lily","Wyatt","Aurora","Matthew","Ellie","Luke","Abigail",
"Gabriel","Penelope","Owen","Hazel","Carter","Luna","Dylan","Madison","Isaac","Evelyn","Caleb","Naomi","Ryan","Avery","Nathan",
"Bella","Julian","Paisley","Adam","Alice","Connor","Maya","Aaron","Leah","Eli","Stella","Anthony","Violet","Christian","Lucy",
"Charles","Brooklyn","Thomas","Elena","Nicholas","Savannah","Hunter","Claire","Sofia","Logan","Daniela","Arthur","Ivy","Max","Nina",
"Oliver","Mila","Ezra","Zoe","Ethan","Noelle","Kai","Ruby","Theo","Piper","Miles","Autumn","Finn","Aurora","Iris","Roman","Skye"]

PLACES = ["Tokyo","London","New York","Sydney","Toronto","Seoul","Paris","Berlin","Barcelona","Singapore","Dublin","Vancouver",
"Osaka","Kyoto","Nagoya","Fukuoka","Sapporo","Los Angeles","San Francisco","Boston","Seattle","Austin","Chicago","Miami",
"Lisbon","Porto","Madrid","Valencia","Milan","Rome","Copenhagen","Stockholm","Helsinki","Zurich","Geneva","Vienna","Prague",
"Warsaw","Tallinn","Reykjavik","Brisbane","Melbourne","Wellington","Cape Town","Johannesburg","Dubai","Doha"]

OBJECTS = ["report","keys","project","ticket","presentation","proposal","email","device","document","package","assignment","meeting",
"dataset","article","draft","budget","contract","timeline","feature","module","test suite","release","poster","whitepaper",
"prototype","pipeline","dashboard","dataset sample","API","service","model","benchmark","experiment","log","memo"]

ADJ = ["important","urgent","draft","updated","final","initial","complex","simple","optional","internal","temporary","archived",
"annotated","baseline","robust","concise","detailed","pilot","production","deprecated"]

ADVERBS = ["briefly","carefully","quickly","quietly","clearly","thoroughly","efficiently","politely","confidently","happily",
"formally","casually","deliberately","explicitly","implicitly","lightly","heavily","randomly","systematically","reliably"]

TIME_PH = ["yesterday","today","last week","this morning","in March","in 2023","two days ago","recently","just now","at noon",
"late at night","on Monday","at 7 a.m.","over the weekend","earlier"]

PUNCT = [".","!","?"]
NUMW = ["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]
MODALS = ["can","could","may","might","must","should","would","has to","ought to","is going to","is likely to","tends to"]
LINKERS = ["For example,","One example:","E.g.,","For instance,","In practice,","Typically,","In many cases,","As a quick demo,","As a note,"]

PP_VERBS = ["has already finished","has already taken","has already submitted","has already lost","has already found",
            "has already booked","has already delivered","has just completed","has recently updated","has never done",
            "has often done","has not yet done","has eventually prepared","has gradually refined"]

PAST_VERBS = ["finished","took","submitted","lost","found","booked","delivered","reviewed","completed","updated",
              "started","checked","approved","finalized","revised","drafted"]

# ===== helpers =====
WORD_RE = re.compile(r"[A-Za-z]+")
def pick(r, seq): return r.choice(seq)

# ---- high-variation generic sentence ----
def make_sentence(r: random.Random, topic: str) -> str:
    name = pick(r,NAMES); place = pick(r,PLACES); obj = pick(r,OBJECTS)
    adv1, adv2 = pick(r,ADVERBS), pick(r,ADVERBS)
    t = pick(r,TIME_PH); num = pick(r,NUMW); punct = pick(r,PUNCT)
    verbs = ["used","applied","leveraged","utilized","employed","practiced","demonstrated","tested","validated","explored"]
    conn  = ["with","on","for","against","via","through"]
    # 20+ schemas
    schemas = [
        "{L} {name} {adv1} {verb} {topic} {conn} the {obj} in {place} {t} ({num}){punct}",
        "{L} In {place}, {name} {verb} {topic} {conn} the {obj} {adv1} {t} ({num}){punct}",
        "{L} The {obj} in {place} was {verb_pp} by {name} while applying {topic} {adv1} {t} ({num}){punct}",
        "{L} {name} {adv1} and {adv2} {verb} {topic} {conn} a {adj} {obj} in {place} {t} ({num}){punct}",
        "{L} While in {place}, {name} {verb} {topic} {conn} the {obj}; outcome noted {t} ({num}){punct}",
        "{L} During a task in {place}, {name} {verb} {topic} {conn} the {obj} {adv1} {t} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} in {place}, {adv1} and concise, {t} ({num}){punct}",
        "{L} In {place}, a {adj} {obj} was handled as {name} {verb} {topic} {adv1} {t} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} in {place} {t} ({num}); insights recorded{punct}",
        "{L} {name} decided to {verb} {topic} {conn} the {obj} at {place} {t} ({num}){punct}",
        "{L} {name} briefly prepared to {verb} {topic} {conn} the {obj} in {place} {t} ({num}){punct}",
        "{L} At {place}, {name} {verb} {topic} {conn} the {obj} {adv1}; report filed {t} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} {adv1} in {place} {t}, then reviewed ({num}){punct}",
        "{L} As a quick check in {place}, {name} {verb} {topic} {conn} the {obj} {t} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} {obj} at {place} {adv1} {t} (ref:{num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} in {place} — {adv1} — {t} ({num}){punct}",
        "{L} In {place} {t}, {name} {verb} {topic} {conn} the {obj} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} in {place} {adv1}; note: {t} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} ({adj}) at {place} {t} ({num}){punct}",
        "{L} {name} {verb} {topic} {conn} the {obj} in {place}; summary added {t} ({num}){punct}",
    ]
    verb = pick(r, verbs); verb_pp = verb + ("ed" if not verb.endswith("e") else "d")
    s = pick(r, schemas).format(
        L=pick(r,LINKERS), name=name, adv1=adv1, adv2=adv2, verb=verb, verb_pp=verb_pp,
        topic=topic, conn=pick(r,conn), obj=obj, place=place, t=t, num=num, punct=punct, adj=pick(r,ADJ)
    )
    # modality / negation tail (可変)
    if r.random() < 0.35:
        tail = " " + pick(r,MODALS)
        if r.random() < 0.4: tail = " not " + pick(r,MODALS)
        s += f" (hint:{tail})"
    return s

# ---- builders ----
def build_generic(r: random.Random, idx: int, topic: str, pattern: str) -> Dict[str,Any]:
    Q = [
        "Write one sentence using the topic: {topic}.",
        "Create a single example sentence that uses {topic}.",
        "Give an example sentence demonstrating {topic}.",
        "Compose one natural sentence employing {topic}.",
        "Provide an illustrative sentence that applies {topic}.",
        "Produce exactly one sentence that showcases {topic}.",
        "Write a concise sentence (~{n} words) using {topic}.",
        "Draft one sentence that clearly demonstrates {topic}.",
        "Supply one sentence featuring {topic} in context.",
        "Generate a single sentence that uses {topic} naturally."
    ]
    q = pick(r,Q).format(topic=topic, n=r.randint(8,18))
    a = make_sentence(r, topic)
    return {"question_en": q, "answer_en": a, "explanation_ja": "多様テンプレで5-gram衝突を低減。",
            "id": f"GRAM-{idx:06d}", "topic": topic, "pattern": pattern,
            "difficulty": pick(r, ["EASY","MEDIUM","HARD"]), "source": "synthetic/local"}

def build_pp_vs_past(r: random.Random, idx: int, topic: str, pattern: str) -> Dict[str,Any]:
    subj=pick(r,NAMES); obj=pick(r,OBJECTS); adj=pick(r,ADJ); place=pick(r,PLACES)
    year=r.randint(2012,2026)
    ppv=pick(r,PP_VERBS); pst=pick(r,PAST_VERBS)
    Q = [
        "How does '{s} {pp} the {a} {o}' differ from '{s} {ps} the {a} {o} in {y}' in {p}?",
        "Explain the difference between '{s} {pp} the {a} {o}' and '{s} {ps} the {a} {o} in {y}' (context: {p}).",
        "Compare: '{s} {pp} the {a} {o}' vs. '{s} {ps} the {a} {o} in {y}'. What is the nuance in {p}?",
        "In meaning and use, how is '{s} {pp} the {a} {o}' different from '{s} {ps} the {a} {o} in {y}' (place: {p})?"
    ]
    A = [
        "Present perfect ties results/experience to now; simple past sits at a finished time.",
        "Present perfect shows present relevance; simple past is detached from the present.",
        "Present perfect links past to now; simple past marks a completed time point.",
        "Present perfect emphasizes now-oriented results; simple past describes a past-only event."
    ]
    q = pick(r,Q).format(s=subj, pp=ppv, ps=pst, a=adj, o=obj, y=year, p=place)
    a = pick(r,A) + f" (loc:{place})"
    return {"question_en": q, "answer_en": a, "explanation_ja": "現在完了は現在関連／過去は時点完了。",
            "id": f"GRAM-{idx:06d}", "topic": topic, "pattern": pattern,
            "difficulty": pick(r, ["EASY","MEDIUM","HARD"]), "source": "synthetic/local"}

def build_article(r: random.Random, idx: int, topic: str, pattern: str) -> Dict[str,Any]:
    nouns = ["apple","umbrella","university","hour","cat","notebook","ocean","house","airport","ring","email","idea","user","error","engineer","orange","issue","update","agreement"]
    templates = [
        "Please hand me __ {noun}.",
        "I bought __ {noun} yesterday.",
        "Close __ door, please.",
        "She is __ engineer in {place}.",
        "He needs __ {noun} for the project.",
        "They opened __ {noun} during the event.",
        "I saw __ {noun} at the station.",
        "We drafted __ {noun} in {place} this morning."
    ]
    noun = pick(r,nouns)
    phr = pick(r,templates).format(noun=noun, place=pick(r,PLACES))
    Q = [
        "Select the appropriate article: '{phr}'{p}",
        "Choose the correct article to complete: '{phr}'{p}",
        "Fill in the blank with the best article: '{phr}'{p}",
        "Which article fits best in: '{phr}'{p}"
    ]
    q = pick(r,Q).format(phr=phr, p=pick(r,PUNCT))
    if noun in ["apple","umbrella","ocean","hour","airport","idea","orange"]:
        ans = "Answer: an"
    elif " door" in phr or " the " in phr.lower():
        ans = "Answer: the"
    elif noun in ["university","house","cat","notebook","ring","user","error","email","engineer","issue","agreement","update"]:
        ans = "Answer: a"
    else:
        ans = "Answer: (no article)"
    return {"question_en": q, "answer_en": ans, "explanation_ja": "母音音→an/子音音→a/特定→the。",
            "id": f"GRAM-{idx:06d}", "topic": "articles (a/an/the/zero)", "pattern": pattern,
            "difficulty": pick(r, ["EASY","MEDIUM"]), "source": "synthetic/local"}

# ---- router ----
def build_item(r: random.Random, idx: int, topic: str, pattern: str) -> Dict[str,Any]:
    if pattern == "contrast_present_perfect_vs_past":
        return build_pp_vs_past(r, idx, topic, pattern)
    if pattern == "choose_correct_article":
        return build_article(r, idx, topic, pattern)
    if pattern.startswith("generic_"):
        return build_generic(r, idx, topic, pattern)
    return build_generic(r, idx, topic, pattern)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recipe", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--deterministic", action="store_true")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--n-per-topic", type=int, default=100)
    args = ap.parse_args()

    r = random.Random(args.seed)
    os.makedirs(args.outdir, exist_ok=True)
    out_path = os.path.join(args.outdir, "english_grammar_qa.jsonl")

    # read recipe
    recipe: List[Dict[str,str]] = []
    with open(args.recipe, "r", encoding="utf-8") as rf:
        for line in rf:
            line=line.strip()
            if not line: continue
            recipe.append(json.loads(line))

    idx=1; kept=0
    with open(out_path,"w",encoding="utf-8") as wf:
        for spec in recipe:
            for _ in range(args.n_per_topic):
                item = build_item(r, idx, spec["topic"], spec["pattern"])
                wf.write(json.dumps(item, ensure_ascii=False)+"\n")
                idx+=1; kept+=1
    print(f"Saved: {out_path}  ({kept} rows)")
    print(f"Recipe lines: {len(recipe)} | per-topic: {args.n_per_topic}")

if __name__ == "__main__":
    main()
