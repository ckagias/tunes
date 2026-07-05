#!/usr/bin/env bash
# Adds every MP3 in SONGS_DIR (see import_to_itunes.conf) to the iTunes library.
#
# Windows-only: this drives classic iTunes for Windows via sync_to_itunes.py's COM
# automation. Run it from Git Bash (or another shell) on native Windows Python.
#
# Usage:
#   ./scripts/import_to_itunes.sh              # uses SONGS_DIR from import_to_itunes.conf
#   ./scripts/import_to_itunes.sh /some/folder # overrides SONGS_DIR for this run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_FILE="$SCRIPT_DIR/import_to_itunes.conf"

if [[ ! -f "$CONF_FILE" ]]; then
  echo "Missing config file: $CONF_FILE" >&2
  exit 1
fi

# shellcheck source=./import_to_itunes.conf
source "$CONF_FILE"

FOLDER="${1:-$SONGS_DIR}"

if [[ -z "${FOLDER:-}" ]]; then
  echo "No folder given and SONGS_DIR is empty in $CONF_FILE" >&2
  exit 1
fi

echo "Importing MP3s from: $FOLDER"
"$PYTHON" "$SCRIPT_DIR/sync_to_itunes.py" "$FOLDER"
