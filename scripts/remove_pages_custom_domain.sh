#!/usr/bin/env bash
# After mint.opsdevco.de aliases to the cluster NLB, drop the Pages custom
# domain only. Do not disable the Pages site. Do not set https_enforced.
set -euo pipefail
REPO="${GITHUB_REPOSITORY:-opsdevcode/specmint-language}"

gh api -X PUT "repos/${REPO}/pages" \
  -f source[branch]=main \
  -f source[path]="/" \
  -f build_type=workflow \
  -F https_enforced=false \
  -f cname=""

gh api "repos/${REPO}/pages" --jq '{cname,https_enforced,html_url,status}'
echo "Pages custom domain removed. Project site remains at opsdevcode.github.io/specmint-language/"
