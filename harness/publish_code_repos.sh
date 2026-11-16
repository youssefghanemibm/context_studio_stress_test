#!/usr/bin/env bash
# Publish the generated code repos (build/code_repo/variant_{a,b,c}) for the GitHub connector test.
#
# The connector ingests a whole repository, so the code corpus must not live on the branch that
# holds this suite. Two layouts are supported:
#
#   branches   orphan branches of THIS repo (default remote: origin)
#                client-codebase           <- variant a  (~350 files, the main connector target)
#                client-codebase-oversize  <- variant b  (600-700 files, truncation canaries)
#                client-codebase-followup  <- variant c  (variant a + 1 follow-up commit, held back)
#
#   repos      separate repositories under an owner (they must already exist and be empty or ours)
#                <owner>/corvane-claims-codebase           main <- variant a
#                <owner>/corvane-claims-codebase-oversize  main <- variant b
#
# Re-sync test (after the first ingestion has finished and been recorded):
#   resync-branch          fast-forwards client-codebase to variant c's head
#   resync-repo <owner>    fast-forwards <owner>/corvane-claims-codebase main to variant c's head
# Variant c shares variant a's history (same commit SHAs), so both are plain fast-forward pushes.
#
# Usage:
#   harness/publish_code_repos.sh branches [remote]
#   harness/publish_code_repos.sh repos <owner>
#   harness/publish_code_repos.sh resync-branch [remote]
#   harness/publish_code_repos.sh resync-repo <owner>
#   harness/publish_code_repos.sh status [remote]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CODE="$ROOT/build/code_repo"
cmd="${1:-}"

need_variant() {
  local v="$1"
  if ! git -C "$CODE/variant_$v" rev-parse --verify -q main >/dev/null; then
    echo "missing build/code_repo/variant_$v (run: .venv/bin/python -I generators/code_repo/assemble.py)" >&2
    exit 1
  fi
}

remote_url() {
  git -C "$ROOT" remote get-url "${1:-origin}"
}

push() {  # push <variant> <url> <dest-ref> [--force-with-lease]
  local v="$1" url="$2" ref="$3"; shift 3
  need_variant "$v"
  local head
  head="$(git -C "$CODE/variant_$v" rev-parse main)"
  echo "variant $v ($head) -> $url $ref"
  git -C "$CODE/variant_$v" push "$@" "$url" "main:$ref"
}

case "$cmd" in
  branches)
    url="$(remote_url "${2:-origin}")"
    push a "$url" refs/heads/client-codebase
    push b "$url" refs/heads/client-codebase-oversize
    push c "$url" refs/heads/client-codebase-followup
    ;;
  repos)
    owner="${2:?owner required, e.g. repos my-github-user}"
    push a "https://github.com/$owner/corvane-claims-codebase.git" refs/heads/main
    push b "https://github.com/$owner/corvane-claims-codebase-oversize.git" refs/heads/main
    ;;
  resync-branch)
    url="$(remote_url "${2:-origin}")"
    push c "$url" refs/heads/client-codebase
    ;;
  resync-repo)
    owner="${2:?owner required}"
    push c "https://github.com/$owner/corvane-claims-codebase.git" refs/heads/main
    ;;
  status)
    url="$(remote_url "${2:-origin}")"
    for v in a b c; do
      printf 'variant %s head: %s\n' "$v" "$(git -C "$CODE/variant_$v" rev-parse --short main 2>/dev/null || echo missing)"
    done
    git ls-remote "$url" 'refs/heads/client-codebase*' || true
    ;;
  *)
    sed -n '2,30p' "$0"
    exit 2
    ;;
esac
