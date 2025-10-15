import argparse, csv, json

COLUMNS = ["id","topic","question_en","answer_en","explanation_ja","difficulty","source"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    with open(a.input, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            obj = json.loads(line)
            rows.append([obj.get(k,"") for k in COLUMNS])

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print(f"Wrote CSV -> {a.out}  ({len(rows)} rows)")

if __name__ == "__main__":
    main()
