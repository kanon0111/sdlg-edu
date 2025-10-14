import argparse, os, zipfile
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--readme", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in (a.data, a.report, a.readme):
            if os.path.exists(p): zf.write(p, arcname=os.path.basename(p))
    print(f"Packaged -> {a.out}")
if __name__ == "__main__": main()
