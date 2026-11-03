#!/usr/bin/env bash
# Validación estática del monorepo. Nunca ejecuta ni hace source de PKGBUILD.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PACKAGES_DIR="$ROOT_DIR/packages"

command -v python3 >/dev/null 2>&1 || {
  printf 'ERROR: python3 no está instalado.\n' >&2
  exit 1
}
command -v bash >/dev/null 2>&1 || {
  printf 'ERROR: bash no está instalado.\n' >&2
  exit 1
}

for script in "$SCRIPT_DIR"/*.sh "$SCRIPT_DIR"/lib/*.sh; do
  [[ -f "$script" ]] || continue
  bash -n "$script" || {
    printf 'ERROR: sintaxis Bash incorrecta en %s\n' "$script" >&2
    exit 1
  }
done

exec python3 "$SCRIPT_DIR/lib/pkgbuild_tools.py" validate "$PACKAGES_DIR"
