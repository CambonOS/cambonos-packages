#!/usr/bin/env bash
# Shared helpers for CambonOS repository maintenance scripts.

cambonos_die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

cambonos_info() {
  printf '\n==> %s\n' "$*"
}

cambonos_require_commands() {
  local command_name
  for command_name in "$@"; do
    command -v "$command_name" >/dev/null 2>&1 ||
      cambonos_die "no se encuentra '$command_name'. Instala las herramientas necesarias."
  done
}

# Packages that were intentionally retired/renamed and must not remain in dist.
# Extend this list when a published package is removed from the monorepo.
CAMBONOS_OBSOLETE_PACKAGES=(cambonos-base)

cambonos_detect_arch() {
  local arch=''

  if command -v pacman-conf >/dev/null 2>&1; then
    arch="$(pacman-conf Architecture 2>/dev/null | sed -n '1p' | tr -d '[:space:]' || true)"
  fi

  if [[ -z "$arch" || "$arch" == 'auto' ]]; then
    arch="$(uname -m)"
  fi

  [[ "$arch" =~ ^[A-Za-z0-9_]+$ ]] ||
    cambonos_die "arquitectura no válida obtenida del sistema: '$arch'"

  printf '%s\n' "$arch"
}

cambonos_acquire_lock() {
  local dist_dir="$1"
  mkdir -p -- "$dist_dir"
  command -v flock >/dev/null 2>&1 ||
    cambonos_die "flock no está disponible (forma parte de util-linux)."

  # FD 9 remains inherited by child scripts, serializing build and publish.
  exec 9>"$dist_dir/.cambonos-repository.lock"
  flock -n 9 || cambonos_die "ya hay otro proceso construyendo o publicando CambonOS."
}
