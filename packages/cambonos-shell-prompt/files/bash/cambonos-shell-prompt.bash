# CambonOS Starship integration for interactive Bash sessions.

case $- in
    *i*) ;;
    *) return 0 ;;
esac

command -v starship >/dev/null 2>&1 || return 0

# Respect an explicit STARSHIP_CONFIG and the user's XDG configuration.
if [[ -z "${STARSHIP_CONFIG:-}" ]]; then
    unset STARSHIP_CONFIG
    if [[ ! -f "${XDG_CONFIG_HOME:-$HOME/.config}/starship.toml" ]]; then
        _cambonos_tty="$(command tty 2>/dev/null || true)"
        if [[ "$_cambonos_tty" =~ ^/dev/tty[0-9]+$ ]]; then
            export STARSHIP_CONFIG='/usr/share/cambonos/shell-prompt/starship-tty.toml'
        else
            export STARSHIP_CONFIG='/usr/share/cambonos/shell-prompt/starship.toml'
        fi
        unset _cambonos_tty
    fi
fi

eval "$(starship init bash)"
