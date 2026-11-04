# CambonOS Fastfetch: all interactive Bash sessions.
# This file is sourced by the managed block in /etc/bash.bashrc.

case $- in
    *i*) ;;
    *) return 0 ;;
esac

# Any non-empty value disables automatic startup.
[[ -n "${CAMBONOS_NO_FASTFETCH:-}" ]] && return 0

# /etc/profile may also load the POSIX login integration.
[[ -n "${_CAMBONOS_FASTFETCH_RAN:-}" ]] && return 0

[[ -x /usr/bin/cambonos-fastfetch ]] || return 0

_CAMBONOS_FASTFETCH_RAN=1
/usr/bin/cambonos-fastfetch
