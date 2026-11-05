# CambonOS Fastfetch: all interactive Zsh sessions.
# Loaded by cambonos-zsh from /usr/share/cambonos/zsh/conf.d/.

[[ -o interactive ]] || return 0

# Any non-empty value disables automatic startup.
[[ -n "${CAMBONOS_NO_FASTFETCH:-}" ]] && return 0

# /etc/profile may also load the POSIX login integration.
[[ -n "${_CAMBONOS_FASTFETCH_RAN:-}" ]] && return 0

[[ -x /usr/bin/cambonos-fastfetch ]] || return 0

_CAMBONOS_FASTFETCH_RAN=1
/usr/bin/cambonos-fastfetch
