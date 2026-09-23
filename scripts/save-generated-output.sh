#!/usr/bin/env bash
set -euo pipefail

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add data output

if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi

git commit -m "data: add daily market summary and HTML"
git push
