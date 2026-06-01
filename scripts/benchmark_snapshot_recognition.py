import argparse
import csv
import glob
import json
import os


def summarize_results(rows):
    total = len(rows)
    accepted = sum(1 for row in rows if row.get("accepted"))
    return {
        "total": total,
        "accepted": accepted,
        "accept_rate": 0.0 if total == 0 else accepted / total,
    }


def _iter_snapshot_paths(input_dir):
    pattern = os.path.join(input_dir, "*", "*", "*.jpg")
    return sorted(glob.glob(pattern))


def build_placeholder_rows(input_dir):
    rows = []
    for path in _iter_snapshot_paths(input_dir):
        parts = os.path.normpath(path).split(os.sep)
        deck_id = parts[-3]
        mat_id = parts[-2]
        rows.append({
            "path": path,
            "deck_id": deck_id,
            "mat_id": mat_id,
            "accepted": False,
            "card_count": 0,
        })
    return rows


def write_csv(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "deck_id", "mat_id", "accepted", "card_count"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    rows = build_placeholder_rows(args.input)
    write_csv(args.output, rows)
    print(json.dumps(summarize_results(rows), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
