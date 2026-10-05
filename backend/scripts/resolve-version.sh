#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BACKEND_DIR="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(CDPATH= cd -- "$BACKEND_DIR/.." && pwd)"
VERSION_FILE="$BACKEND_DIR/cmd/server/VERSION"

# Only a fork release tag may override VERSION. Upstream tags can coexist locally.
if command -v git >/dev/null 2>&1; then
  TAG="$(
    git -C "$REPO_DIR" tag --points-at HEAD 2>/dev/null | \
      LC_ALL=C sort -rV | \
      sed -nE '/^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?-[1-9][0-9]*$/p' | \
      head -n 1
  )"
  if [ -n "$TAG" ]; then
    printf '%s\n' "${TAG#v}"
    exit 0
  fi
fi

printf '%s\n' "$(tr -d '\r\n' < "$VERSION_FILE")"
