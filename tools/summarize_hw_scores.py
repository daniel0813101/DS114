#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_handin_time(value):
    return value.strip() if value else ""


def summarize_hw(hw_dir):
    problem_score_files = sorted(hw_dir.glob("*/score.csv"))
    totals = defaultdict(lambda: {"name": "", "student_id": "", "score": 0, "handin_time": ""})

    for score_file in problem_score_files:
        with score_file.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student_id = (row.get("student_id") or "").strip()
                if not student_id:
                    continue

                name = (row.get("name") or "").strip()
                score_text = (row.get("score") or "0").strip()
                handin_time = parse_handin_time(row.get("handin_time") or "")

                try:
                    score = int(float(score_text))
                except ValueError:
                    score = 0

                record = totals[student_id]
                if not record["name"]:
                    record["name"] = name
                record["student_id"] = student_id
                record["score"] += score
                if handin_time and handin_time > record["handin_time"]:
                    record["handin_time"] = handin_time

    output_path = hw_dir / "score.csv"
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "student_id", "score", "handin_time"])
        writer.writeheader()
        for student_id in sorted(totals.keys()):
            writer.writerow(totals[student_id])

    return output_path, len(problem_score_files), len(totals)


def summarize_all_hw(score_root):
    hw_score_files = sorted(score_root.glob("*/score.csv"))
    hw_columns = [
        ("HW_1", "HW1"),
        ("HW_2", "HW2"),
        ("HW_3", "HW3"),
        ("HW_4", "HW4"),
        ("HW_5", "HW5"),
        ("Midterm", "Midterm"),
        ("HW_6", "HW6"),
        ("HW_7", "HW7"),
        ("HW_8", "HW8"),
        ("HW_9", "HW9"),
        ("Final", "Final"),
    ]
    hw_name_to_column = dict(hw_columns)
    output_columns = [column for _, column in hw_columns]
    totals = defaultdict(lambda: {"name": "", "student_id": "", "scores": {}})

    for score_file in hw_score_files:
        if score_file.parent == score_root:
            continue

        hw_name = score_file.parent.name
        column_name = hw_name_to_column.get(hw_name)
        if column_name is None:
            continue

        with score_file.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                student_id = (row.get("student_id") or "").strip()
                if not student_id:
                    continue

                name = (row.get("name") or "").strip()
                score_text = (row.get("score") or "0").strip()
                handin_time = parse_handin_time(row.get("handin_time") or "")

                try:
                    score = int(float(score_text))
                except ValueError:
                    score = 0

                record = totals[student_id]
                if not record["name"]:
                    record["name"] = name
                record["student_id"] = student_id
                record["scores"][column_name] = score

    output_path = score_root / "all_hw_score.csv"
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["name", "student_id", *output_columns]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for student_id in sorted(totals.keys()):
            record = totals[student_id]
            row = {
                "name": record["name"],
                "student_id": record["student_id"],
            }
            scores = record.get("scores", {})
            for column_name in output_columns:
                row[column_name] = scores.get(column_name, 0)
            writer.writerow(row)

    return output_path, len(hw_score_files), len(totals)


def main():
    parser = argparse.ArgumentParser(description="Summarize per-problem score.csv files into one homework score.csv.")
    parser.add_argument("--hw-dir", help="Homework directory, e.g. score/HW_2")
    parser.add_argument("--score-root", help="Root score directory, e.g. score")
    parser.add_argument("--all", action="store_true", help="Aggregate all HW score.csv files under the score root")
    args = parser.parse_args()

    if args.all:
        if not args.score_root:
            raise SystemExit("--score-root is required when using --all")
        score_root = Path(args.score_root)
        if not score_root.exists():
            raise SystemExit(f"Score root directory not found: {score_root}")
        output_path, hw_count, student_count = summarize_all_hw(score_root)
        print(f"Wrote {output_path} from {hw_count} homework score files for {student_count} students.")
        return

    if not args.hw_dir:
        raise SystemExit("--hw-dir is required unless --all is used")

    hw_dir = Path(args.hw_dir)
    if not hw_dir.exists():
        raise SystemExit(f"Homework directory not found: {hw_dir}")

    output_path, problem_count, student_count = summarize_hw(hw_dir)
    print(f"Wrote {output_path} from {problem_count} problem files for {student_count} students.")


if __name__ == "__main__":
    main()
