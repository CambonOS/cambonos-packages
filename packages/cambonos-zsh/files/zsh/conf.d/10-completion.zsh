# CambonOS: completion system.

# Make the additional completion definitions available before compinit.
if [[ -d /usr/share/zsh/site-functions ]]; then
    fpath=(/usr/share/zsh/site-functions $fpath)
fi

# Keep completion cache files private and outside the user's home root.
_cambonos_zsh_cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
if [[ ! -d "$_cambonos_zsh_cache_dir" ]]; then
    ( umask 077; command mkdir -p -- "$_cambonos_zsh_cache_dir" ) 2>/dev/null
fi

zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{[:lower:]}={[:upper:]}' 'm:{[:upper:]}={[:lower:]}'
zstyle ':completion:*' special-dirs true
zstyle ':completion:*' squeeze-slashes true
zstyle ':completion:*' list-colors ''

autoload -Uz compinit
if [[ -d "$_cambonos_zsh_cache_dir" ]]; then
    compinit -d "$_cambonos_zsh_cache_dir/zcompdump-$ZSH_VERSION"
else
    compinit
fi

unset _cambonos_zsh_cache_dir
