# CambonOS: Emacs editing mode and terminal key bindings.

bindkey -e
zmodload zsh/terminfo 2>/dev/null || true

# Home/End move within the current editing line; Delete removes the character
# under the cursor. PageUp/PageDown search history using the current prefix.
[[ -n "${terminfo[khome]-}" ]] && bindkey -M emacs "${terminfo[khome]}" beginning-of-line
[[ -n "${terminfo[kend]-}"  ]] && bindkey -M emacs "${terminfo[kend]}" end-of-line
[[ -n "${terminfo[kdch1]-}" ]] && bindkey -M emacs "${terminfo[kdch1]}" delete-char
[[ -n "${terminfo[kpp]-}"   ]] && bindkey -M emacs "${terminfo[kpp]}" history-beginning-search-backward
[[ -n "${terminfo[knp]-}"   ]] && bindkey -M emacs "${terminfo[knp]}" history-beginning-search-forward

# Common xterm-compatible fallbacks for terminals with incomplete terminfo.
bindkey -M emacs '^[[H' beginning-of-line
bindkey -M emacs '^[[F' end-of-line
bindkey -M emacs '^[[3~' delete-char
bindkey -M emacs '^[[5~' history-beginning-search-backward
bindkey -M emacs '^[[6~' history-beginning-search-forward
