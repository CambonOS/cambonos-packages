# CambonOS Fastfetch: every interactive Fish shell (login or non-login).
if status is-interactive
    and not set -q CAMBONOS_NO_FASTFETCH
    and command -q cambonos-fastfetch
    cambonos-fastfetch
end
