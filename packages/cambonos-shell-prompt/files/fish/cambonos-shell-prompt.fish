# CambonOS Starship integration for interactive Fish sessions.

if status is-interactive; and command -q starship
    if set -q STARSHIP_CONFIG; and test -z "$STARSHIP_CONFIG"
        set -e STARSHIP_CONFIG
    end
    if not set -q STARSHIP_CONFIG
        set -l _cambonos_starship_config_home "$HOME/.config"
        if set -q XDG_CONFIG_HOME; and test -n "$XDG_CONFIG_HOME"
            set _cambonos_starship_config_home "$XDG_CONFIG_HOME"
        end
        if not test -f "$_cambonos_starship_config_home/starship.toml"
            set -gx STARSHIP_CONFIG /usr/share/cambonos/shell-prompt/starship.toml
        end
        set -e _cambonos_starship_config_home
    end

    starship init fish | source
end
