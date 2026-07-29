#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$ROOT/sample-permissions.yaml"
TARGET_DIR="$HOME/.kiro/settings"
TARGET="$TARGET_DIR/permissions.yaml"
STAMP="$(date +%Y%m%d-%H%M%S)"
CANDIDATE="$TARGET_DIR/permissions.workshop-$STAMP.yaml"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

cat <<EOF
Kiro stores permissions outside repositories.
Source rules: $SOURCE
User target:  $TARGET
EOF

if [[ "$DRY_RUN" == true ]]; then
  echo "No files changed. Review and manually merge these rules:"
  cat "$SOURCE"
  exit 0
fi

mkdir -p "$TARGET_DIR"
if [[ -e "$TARGET" ]]; then
  cp "$SOURCE" "$CANDIDATE"
  cat <<EOF
Existing permissions were NOT overwritten.
A merge candidate was written to:
  $CANDIDATE
Review both files and merge only rules you accept:
  $TARGET
  $CANDIDATE
EOF
else
  cp "$SOURCE" "$TARGET"
  chmod 600 "$TARGET"
  echo "Created $TARGET. Review it before starting Kiro."
fi
