import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.ingest.importer import import_all

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Re-import even if already imported")
    args = ap.parse_args()
    res = import_all(force=args.force)
    for k, v in res.items():
        print(f"{k}: {v}")