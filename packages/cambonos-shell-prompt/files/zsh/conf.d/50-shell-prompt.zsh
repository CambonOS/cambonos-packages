# CambonOS Starship integration for Zsh.
# Loaded by cambonos-zsh from /usr/share/cambonos/zsh/conf.d/.

[[ -o interactive ]] || return 0
(( $+commands[starship] )) || return 0

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

eval "$(starship init zsh)"
