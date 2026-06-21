#!/usr/bin/env bash
set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$TOOLS_DIR/.." && pwd)"
CRAWLER="$ROOT_DIR/tools/crawler.py"
SUMMARIZER="$ROOT_DIR/tools/summarize_hw_scores.py"
SCORE_ROOT="$ROOT_DIR/score"
STUDENTS_FILE="$ROOT_DIR/tools/students.csv"

run_one() {
  local hw_name="$1"
  local problem_id="$2"
  local deadline="$3"
  local output_dir="$SCORE_ROOT/$hw_name/$problem_id"

  mkdir -p "$output_dir"
  echo "Running $hw_name problem $problem_id -> $output_dir"
  python3 "$CRAWLER" \
    --problem-id "$problem_id" \
    --deadline "$deadline" \
    --report-folder "$output_dir" \
    --students-file "$STUDENTS_FILE"
}

summarize_hw() {
  local hw_name="$1"
  local hw_dir="$SCORE_ROOT/$hw_name"

  if [ -d "$hw_dir" ]; then
    python3 "$SUMMARIZER" --hw-dir "$hw_dir"
  fi
}

run_one "HW_1" "2083" "2026-03-27_23:59:59"
run_one "HW_1" "2086" "2026-03-27_23:59:59"
summarize_hw "HW_1"

run_one "HW_2" "2088" "2026-04-03_23:59:59"
run_one "HW_2" "2089" "2026-04-03_23:59:59"
summarize_hw "HW_2"

run_one "HW_3" "2091" "2026-04-10_23:59:59"
run_one "HW_3" "2092" "2026-04-10_23:59:59"
summarize_hw "HW_3"

run_one "HW_4" "2098" "2026-04-24_23:59:59"
summarize_hw "HW_4"

run_one "Midterm" "2134" "2026-04-24_17:30:00"
summarize_hw "Midterm"

run_one "HW_5" "2375" "2026-05-15_23:59:59"
summarize_hw "HW_5"

run_one "HW_6" "2112" "2026-05-22_23:59:59"
summarize_hw "HW_6"

run_one "HW_7" "2380" "2026-05-29_23:59:59"
summarize_hw "HW_7"

run_one "HW_8" "2151" "2026-06-05_23:59:59"
run_one "HW_8" "2152" "2026-06-05_23:59:59"
summarize_hw "HW_8"

run_one "HW_9" "2149" "2026-06-12_23:59:59"
run_one "HW_9" "2150" "2026-06-12_23:59:59"
summarize_hw "HW_9"

run_one "Final" "2161" "2026-06-12_16:20:00"
run_one "Final" "2162" "2026-06-12_16:20:00"
run_one "Final" "2394" "2026-06-12_16:20:00"
summarize_hw "Final"

python3 "$SUMMARIZER" --score-root "$SCORE_ROOT" --all

echo "Done"
