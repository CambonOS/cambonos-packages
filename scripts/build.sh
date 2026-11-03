#!/usr/bin/env bash
# Construye todos los paquetes y publica sus artefactos de forma transaccional.
# Las dependencias de ejecución no tienen que estar instaladas en el host:
# makepkg --nodeps las conserva en el paquete, pero omite su comprobación local.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PACKAGES_DIR="$ROOT_DIR/packages"
DIST_DIR="$ROOT_DIR/dist"

# repo-add.sh mantiene el mismo bloqueo y llama a build.sh con --lock-held.
LOCK_HELD=0
case "${1:-}" in
  '') ;;
  --lock-held) LOCK_HELD=1 ;;
  -h|--help)
    printf 'Uso: %s [--lock-held]\n' "$0"
    printf 'Construye todos los paquetes y actualiza los artefactos de dist/<arquitectura>.\n'
    exit 0
    ;;
  *)
    printf 'Argumento no reconocido: %s\n' "$1" >&2
    printf 'Uso: %s [--lock-held]\n' "$0" >&2
    exit 2
    ;;
esac

# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
cambonos_require_commands makepkg pacman python3 find mv rm mktemp sort sed tr

if (( LOCK_HELD == 0 )); then
  cambonos_acquire_lock "$DIST_DIR"
fi

# Validation is always part of a build, even when build.sh is called directly.
cambonos_info 'Validando los PKGBUILD y los archivos fuente'
"$SCRIPT_DIR/validate.sh"

mapfile -d '' -t PKGBUILDS < <(
  find "$PACKAGES_DIR" -mindepth 2 -maxdepth 2 -type f -name PKGBUILD -print0 | sort -z
)
(( ${#PKGBUILDS[@]} > 0 )) || cambonos_die "no se encontraron PKGBUILD en $PACKAGES_DIR"

ARCH="$(cambonos_detect_arch)"
ARCH_DIST_DIR="$DIST_DIR/$ARCH"
mkdir -p -- "$ARCH_DIST_DIR"
BUILD_TMP_DIR="$(mktemp -d "$DIST_DIR/.build.${ARCH}.XXXXXX")"
STAGE_ROOT="$BUILD_TMP_DIR/stage"
BACKUP_DIR="$BUILD_TMP_DIR/backup"
mkdir -p -- "$STAGE_ROOT" "$BACKUP_DIR"

PACKAGE_DIRS=()
PACKAGE_NAMES=()
NEW_FILES=()
BACKUP_FILES=()
COMMIT_STARTED=0
COMMIT_DONE=0

rollback_commit() {
  local path
  (( COMMIT_STARTED == 1 && COMMIT_DONE == 0 )) || return 0

  printf '\nAVISO: revirtiendo la publicación incompleta de paquetes...\n' >&2
  for path in "${NEW_FILES[@]}"; do
    rm -f -- "$path" || true
  done
  for path in "${BACKUP_FILES[@]}"; do
    if [[ -e "$path" || -L "$path" ]]; then
      mv -fT -- "$path" "$ARCH_DIST_DIR/" || true
    fi
  done
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  rollback_commit

  # makepkg owns these transient directories. Never remove files/ (sources).
  local package_dir
  for package_dir in "${PACKAGE_DIRS[@]}"; do
    rm -rf -- "$package_dir/src" "$package_dir/pkg"
    find "$package_dir" -maxdepth 1 -type f -name '*.pkg.tar.*' -delete
  done

  rm -rf -- "$BUILD_TMP_DIR"
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

BUILT_COUNT=0
for pkgbuild in "${PKGBUILDS[@]}"; do
  package_dir="$(dirname -- "$pkgbuild")"
  package_name="$(basename -- "$package_dir")"
  PACKAGE_DIRS+=("$package_dir")
  PACKAGE_NAMES+=("$package_name")

  package_stage="$STAGE_ROOT/$package_name"
  mkdir -p -- "$package_stage"

  cambonos_info "Construyendo $package_name para $ARCH"
  (
    cd -- "$package_dir"
    PKGDEST="$package_stage" makepkg \
      --nodeps \
      --cleanbuild \
      --clean \
      --force \
      --noconfirm
  )

  shopt -s nullglob
  artifacts=("$package_stage"/*.pkg.tar.*)
  valid_artifacts=()
  for artifact in "${artifacts[@]}"; do
    [[ "$artifact" == *.sig ]] && continue
    [[ -f "$artifact" ]] || continue

    actual_name="$(pacman -Qqp "$artifact")" ||
      cambonos_die "no se puede leer la metadata del paquete generado: $artifact"
    [[ "$actual_name" == "$package_name" ]] ||
      cambonos_die "$package_name generó un paquete inesperado: $actual_name ($artifact)"
    valid_artifacts+=("$artifact")
  done

  (( ${#valid_artifacts[@]} > 0 )) ||
    cambonos_die "makepkg no ha generado ningún paquete válido para $package_name"

  for artifact in "${valid_artifacts[@]}"; do
    printf '  Preparado: %s\n' "$(basename -- "$artifact")"
    BUILT_COUNT=$((BUILT_COUNT + 1))
  done
done

(( BUILT_COUNT > 0 )) || cambonos_die 'no se ha generado ningún paquete.'

# Commit starts only after every PKGBUILD has built and every archive passed
# pacman metadata inspection. Previous package archives are kept for rollback.
cambonos_info "Publicando $BUILT_COUNT paquete(s) en dist/$ARCH"
COMMIT_STARTED=1

# Exact package names are read from archive metadata to avoid prefix collisions
# (for example, package 'foo' versus 'foo-tools'). The former package name is
# included because cambonos-base was split into cambonos-release/fastfetch.
declare -A REPLACED_NAMES=()
for package_name in "${PACKAGE_NAMES[@]}"; do
  REPLACED_NAMES["$package_name"]=1
done
for obsolete_name in "${CAMBONOS_OBSOLETE_PACKAGES[@]}"; do
  REPLACED_NAMES["$obsolete_name"]=1
done

shopt -s nullglob
existing_archives=("$ARCH_DIST_DIR"/*.pkg.tar.*)
for existing in "${existing_archives[@]}"; do
  [[ "$existing" == *.sig ]] && continue
  [[ -f "$existing" ]] || continue
  existing_name="$(pacman -Qqp "$existing")" ||
    cambonos_die "hay un paquete inválido en el repositorio: $existing"

  if [[ -n "${REPLACED_NAMES[$existing_name]+x}" ]]; then
    backup_path="$BACKUP_DIR/$(basename -- "$existing")"
    mv -T -- "$existing" "$backup_path"
    BACKUP_FILES+=("$backup_path")
    if [[ -f "$existing.sig" ]]; then
      mv -T -- "$existing.sig" "$backup_path.sig"
      BACKUP_FILES+=("$backup_path.sig")
    fi
  fi
done

for pkgbuild in "${PKGBUILDS[@]}"; do
  package_name="$(basename -- "$(dirname -- "$pkgbuild")")"
  package_stage="$STAGE_ROOT/$package_name"
  staged_artifacts=("$package_stage"/*.pkg.tar.*)
  for artifact in "${staged_artifacts[@]}"; do
    [[ "$artifact" == *.sig ]] && continue
    destination="$ARCH_DIST_DIR/$(basename -- "$artifact")"
    mv -T -- "$artifact" "$destination"
    NEW_FILES+=("$destination")
  done
done

COMMIT_DONE=1
printf '\nConstrucción completada: %d paquete(s).\n' "$BUILT_COUNT"
printf 'Artefactos publicados en: %s\n' "$ARCH_DIST_DIR"
printf 'La base de datos se actualiza con scripts/repo-add.sh.\n'
