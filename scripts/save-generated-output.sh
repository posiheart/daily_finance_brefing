#!/usr/bin/env bash
set -euo pipefail

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
# `output/` is intentionally ignored for local development, so it must be
# forced into the daily snapshot commit. Without `--force`, `git add` exits
# with status 1 and stops the workflow before the Pages deployment.
git add data
git add --force output

if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi

git commit -m "data: add daily market summary and HTML"
git push
