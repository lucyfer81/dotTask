#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="${1:-$DIR/dotTask.zip}"

echo "Packaging to $OUTPUT ..."

zip -r "$OUTPUT" \
  CLAUDE.md \
  config.py \
  run.py \
  requirements.txt \
  taskmgr.sh \
  APAC_Infra_Task_List.xlsx \
  config/ \
  docs/ \
  app/__init__.py \
  app/dropdowns.py \
  app/models.py \
  app/routes/ \
  app/services/ \
  app/static/ \
  app/templates/ \
  -x "*.pyc" "*__pycache__*"

echo "Done: $(du -sh "$OUTPUT" | cut -f1)"
