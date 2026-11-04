# CambonOS Fastfetch: all interactive Fish sessions.

if status is-interactive
    and not set -q _CAMBONOS_FASTFETCH_RAN
    and not test -n "$CAMBONOS_NO_FASTFETCH"
    and command -q cambonos-fastfetch

    set -g _CAMBONOS_FASTFETCH_RAN 1
    cambonos-fastfetch
end
