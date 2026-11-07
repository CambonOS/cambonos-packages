# CambonOS: persistent interactive history.

HISTFILE="${ZDOTDIR:-$HOME}/.zsh_history"
HISTSIZE=100000
SAVEHIST=100000

setopt append_history
setopt extended_history
setopt hist_ignore_dups
setopt hist_reduce_blanks

# Retain the familiar CambonOS interactive behaviour.
setopt autocd
setopt correct

alias ls='ls --color=auto'
alias untar='tar -xvf'
alias targz='tar -czvf'
alias untargz='tar -xzvf'
