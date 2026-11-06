# CambonOS: elevate pacman operations that modify system state.
#
# Queries remain unprivileged. Root never invokes sudo through this wrapper.

_cambonos_pacman_needs_sudo() {
    local arg operation='' flags='' found=0 operation_token=''
    local flag i

    # Help and version requests are always read-only.
    for arg in "$@"; do
        [[ "$arg" == -- ]] && break
        case "$arg" in
            --help|--version) return 1 ;;
            -[!-]*)
                if [[ "$arg" == *h* || "$arg" == *V* ]]; then
                    return 1
                fi
                ;;
        esac
    done

    # Locate the operation, supporting short and long forms.
    for arg in "$@"; do
        [[ "$arg" == -- ]] && break
        case "$arg" in
            --database) operation=D; operation_token="$arg"; found=1 ;;
            --files)    operation=F; operation_token="$arg"; found=1 ;;
            --query)    operation=Q; operation_token="$arg"; found=1 ;;
            --remove)   operation=R; operation_token="$arg"; found=1 ;;
            --sync)     operation=S; operation_token="$arg"; found=1 ;;
            --deptest)  operation=T; operation_token="$arg"; found=1 ;;
            --upgrade)  operation=U; operation_token="$arg"; found=1 ;;
            -[!-]*)
                for (( i = 2; i <= ${#arg}; ++i )); do
                    flag="${arg[i]}"
                    case "$flag" in
                        D|F|Q|R|S|T|U|V|h)
                            operation="$flag"
                            operation_token="$arg"
                            found=1
                            if (( i < ${#arg} )); then
                                flags+="${arg[$((i + 1)),-1]}"
                            fi
                            break
                            ;;
                    esac
                done
                ;;
        esac
        (( found )) && break
    done

    (( found )) || return 1

    # Collect modifiers following the operation. For long options, map only
    # the pacman flags relevant to distinguishing read-only sync/file queries.
    local after_operation=0
    for arg in "$@"; do
        if (( ! after_operation )); then
            if [[ "$arg" == "$operation_token" ]]; then
                after_operation=1
            fi
            continue
        fi

        [[ "$arg" == -- ]] && break
        case "$arg" in
            --refresh)      flags+=y ;;
            --sysupgrade)   flags+=u ;;
            --clean)        flags+=c ;;
            --downloadonly) flags+=w ;;
            --force)        flags+=f ;;
            --check)        flags+=k ;;
            --groups)       flags+=g ;;
            --info)         flags+=i ;;
            --list)         flags+=l ;;
            --print)        flags+=p ;;
            --search)       flags+=s ;;
            -[!-]*)
                for (( i = 2; i <= ${#arg}; ++i )); do
                    flags+="${arg[i]}"
                done
                ;;
        esac
    done

    case "$operation" in
        Q|T|V|h)
            return 1
            ;;
        F)
            # -Fy refreshes the files database; ordinary -F operations query it.
            [[ "$flags" == *y* ]] && return 0
            return 1
            ;;
        S)
            # These options can modify system state and take precedence over
            # query modifiers if a user combines them.
            if [[ "$flags" == *y* || "$flags" == *u* || "$flags" == *c* ||
                  "$flags" == *w* || "$flags" == *f* || "$flags" == *k* ]]; then
                return 0
            fi
            if [[ "$flags" == *g* || "$flags" == *i* || "$flags" == *l* ||
                  "$flags" == *p* || "$flags" == *s* ]]; then
                return 1
            fi
            return 0
            ;;
        D|R|U)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

pacman() {
    if (( EUID == 0 )); then
        command pacman "$@"
        return $?
    fi

    if _cambonos_pacman_needs_sudo "$@"; then
        command sudo pacman "$@"
    else
        command pacman "$@"
    fi
}
