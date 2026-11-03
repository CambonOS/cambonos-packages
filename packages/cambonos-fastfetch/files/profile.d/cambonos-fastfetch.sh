# CambonOS Fastfetch: interactive login shells using /etc/profile.
# Bash and Zsh also have dedicated global interactive entry points.

case $- in
    *i*) ;;
    *) return 0 ;;
esac

[ -n "${CAMBONOS_NO_FASTFETCH:-}" ] && return 0
[ -n "${_CAMBONOS_FASTFETCH_RAN:-}" ] && return 0
[ -x /usr/bin/cambonos-fastfetch ] || return 0

_CAMBONOS_FASTFETCH_RAN=1
/usr/bin/cambonos-fastfetch
