#!/usr/bin/env bash
# Punto de entrada único: valida, construye y actualiza la base de datos pacman.
# La publicación conserva una copia de la arquitectura y la restaura si falla.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"

case "${1:-}" in
  '') ;;
  -h|--help)
    printf 'Uso: %s\n' "$0"
    printf 'Valida, construye todos los paquetes y actualiza cambonos.db/cambonos.files.\n'
    exit 0
    ;;
  *)
    printf 'Argumento no reconocido: %s\n' "$1" >&2
    printf 'Uso: %s\n' "$0" >&2
    exit 2
    ;;
esac

# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
cambonos_require_commands repo-add pacman tar cp mv rm mktemp find sort sed tr
cambonos_acquire_lock "$DIST_DIR"

ARCH="$(cambonos_detect_arch)"
ARCH_DIST_DIR="$DIST_DIR/$ARCH"
ARCH_DIR_EXISTED=0
if [[ -d "$ARCH_DIST_DIR" ]]; then
  ARCH_DIR_EXISTED=1
fi
mkdir -p -- "$ARCH_DIST_DIR"

PUBLISH_TMP_DIR="$(mktemp -d "$DIST_DIR/.publish.${ARCH}.XXXXXX")"
BACKUP_DIR="$PUBLISH_TMP_DIR/previous-architecture"
DB_STAGE_DIR="$PUBLISH_TMP_DIR/database"
mkdir -p -- "$BACKUP_DIR" "$DB_STAGE_DIR"

PUBLISH_COMMITTED=0
SNAPSHOT_READY=0
restore_previous_repository() {
  local status=$?
  trap - EXIT INT TERM

  if (( PUBLISH_COMMITTED == 0 && SNAPSHOT_READY == 1 )); then
    printf '\nERROR: la publicación no se completó; restaurando dist/%s.\n' "$ARCH" >&2
    find "$ARCH_DIST_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + 2>/dev/null || true
    cp -a -- "$BACKUP_DIR/." "$ARCH_DIST_DIR/" || true
    if (( ARCH_DIR_EXISTED == 0 )); then
      rmdir -- "$ARCH_DIST_DIR" 2>/dev/null || true
    fi
  fi

  rm -rf -- "$PUBLISH_TMP_DIR"
  exit "$status"
}
trap restore_previous_repository EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Snapshot the complete architecture directory, including old DB links and
# package signatures, so a failed indexing step cannot strand the old repo.
cp -a -- "$ARCH_DIST_DIR/." "$BACKUP_DIR/"
SNAPSHOT_READY=1

cambonos_info 'Construyendo todos los paquetes'
"$SCRIPT_DIR/build.sh" --lock-held

shopt -s nullglob
package_files=("$ARCH_DIST_DIR"/*.pkg.tar.*)
valid_packages=()
for package_file in "${package_files[@]}"; do
  [[ "$package_file" == *.sig ]] && continue
  [[ -f "$package_file" ]] || continue
  package_name="$(pacman -Qqp "$package_file")" ||
    cambonos_die "paquete inválido en dist: $package_file"
  valid_packages+=("$package_file")
done

(( ${#valid_packages[@]} > 0 )) || cambonos_die "no hay paquetes válidos para indexar en $ARCH_DIST_DIR"

# Build a fresh database from the complete set of current archives. This
# naturally drops obsolete entries (including cambonos-base) without relying
# on repo-remove or mutating the live database before the replacement is ready.
cambonos_info "Generando la base de datos para $ARCH"
STAGED_DB="$DB_STAGE_DIR/cambonos.db.tar.gz"
repo-add "$STAGED_DB" "${valid_packages[@]}"

for required_file in cambonos.db.tar.gz cambonos.db cambonos.files.tar.gz cambonos.files; do
  if [[ ! -e "$DB_STAGE_DIR/$required_file" && ! -L "$DB_STAGE_DIR/$required_file" ]]; then
    cambonos_die "repo-add no ha generado el archivo esperado: $required_file"
  fi
done

# Replace database files only after the complete new database is available.
# The outer snapshot provides rollback if any rename fails.
for database_file in cambonos.files.tar.gz cambonos.files cambonos.db.tar.gz cambonos.db; do
  mv -fT -- "$DB_STAGE_DIR/$database_file" "$ARCH_DIST_DIR/$database_file"
done

# Do not leave stale signatures next to newly generated unsigned databases.
rm -f -- "$ARCH_DIST_DIR/cambonos.db.tar.gz.sig" "$ARCH_DIST_DIR/cambonos.files.tar.gz.sig"

PUBLISH_COMMITTED=1
printf '\n==============================================\n'
printf 'Repositorio CambonOS actualizado correctamente.\n'
printf 'Arquitectura:       %s\n' "$ARCH"
printf 'Paquetes indexados: %d\n' "${#valid_packages[@]}"
printf 'Base de datos:      %s\n' "$ARCH_DIST_DIR/cambonos.db.tar.gz"
printf '==============================================\n'
