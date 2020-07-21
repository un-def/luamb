# shellcheck shell=bash

# This file is both valid Shell script and Python module.
#
# It can be sourced in shell:
# $ source _shell.py
#
# And it can be imported in Python:
# $ python -c 'import _shell; print(_shell.shellsrc)'

"""":

# Dependencies
#
#   readlink (or greadlink)
#   basename
#   cat
#   uname
#   sed
#   find (for completions)
#
# Exported variables
#
#   LUAMB_ACTIVE_ENV
#       A name of the active environment or an empty string.
#
# Global variables
#
#   __luamb_readlink
#       A name of the readlink binary ('readlink' or 'greadlink').
#
#   __luamb_orig_ps1
#       The original value of the PS1 variable.
#       Unset if no active environment.
#
# Functions (in addition to those explicitly declared at the top level)
#
#    __luamb_orig_deactivate
#       The renamed original 'deactivate-lua'.
#       Unset if no active environment.


__luamb_check_exists() {
    type "$@" > /dev/null 2>&1
}


__luamb_is_active() {
    __luamb_check_exists deactivate-lua
}


__luamb_wrap_deactivate_function() {
    local __luamb_orig_deactivate_code
    __luamb_orig_deactivate_code=$(typeset -f deactivate-lua | \
        sed 's/deactivate-lua/__luamb_orig_deactivate/g')
    eval "$__luamb_orig_deactivate_code"
    deactivate-lua() {
        __luamb_off
    }
}


__luamb_on() {
    local env_name
    # tricky way to prevent slashes in env name
    env_name=$(basename "$1")
    local env_path
    env_path=$($__luamb_readlink -e "$LUAMB_DIR/$env_name")
    if [ ! -d "$env_path" ]; then
        echo "environment doesn't exist: $env_name"
        return 1
    fi
    if __luamb_is_active; then
        __luamb_off
    fi
    __luamb_orig_ps1=$PS1
    PS1="($env_name) $__luamb_orig_ps1"
    LUAMB_ACTIVE_ENV=$env_name
    # shellcheck disable=SC1090
    source "$env_path/bin/activate"
    __luamb_wrap_deactivate_function
    if [ -f "$env_path/.project" ]; then
        # shellcheck disable=SC2164
        cd "$(cat "$env_path/.project")"
    fi
    echo "environment activated: $env_name"
}


__luamb_off() {
    if __luamb_is_active; then
        __luamb_orig_deactivate
        unset -f deactivate-lua
        echo "environment deactivated: $LUAMB_ACTIVE_ENV"
        PS1=$__luamb_orig_ps1
        unset __luamb_orig_ps1
        LUAMB_ACTIVE_ENV=""
    else
        echo "no active environment"
    fi
}


__luamb_cmd() {
    local cmd
    if [ -n "$LUAMB_PYTHON_BIN" ]; then
        cmd=("$LUAMB_PYTHON_BIN" -m luamb "$@")
    else
        cmd=(command luamb "$@")
    fi
    "${cmd[@]}"
    return $?
}


luamb() {
    case "$1" in
        on|enable|activate)
            if [ -z "$2" ]; then
                echo "usage: luamb on ENV_NAME"
                return 1
            fi
            __luamb_on "$2"
            ;;
        off|disable|deactivate)
            __luamb_off
            ;;
        *)
            __luamb_cmd "$@"
    esac
}


if [ -z "$LUAMB_DIR" ]; then
    echo "LUAMB_DIR variable not set"
    return 1
fi

if [ "$(uname)" = "Darwin" ]; then
    __luamb_readlink="greadlink"
    if ! __luamb_check_exists $__luamb_readlink; then
        echo "luamb: greadlink not found, install coreutils:"
        echo "brew install coreutils"
        return 1
    fi
else
    __luamb_readlink="readlink"
fi

export LUAMB_ACTIVE_ENV=""

if [ "$LUAMB_DISABLE_COMPLETION" != "true" ]; then
    __luamb_completion() {
        case "$1" in
            luamb)
                COMPLETION_OPTS="on enable activate \
                                 off disable deactivate \
                                 mk new create \
                                 rm remove del delete \
                                 info show \
                                 ls list"
                ;;
            on|enable|activate|rm|remove|del|delete|info|show)
                COMPLETION_OPTS=$(find "$LUAMB_DIR" -mindepth 1 -maxdepth 1 \
                                  -type d -printf "%f ")
                ;;
            *)
                COMPLETION_OPTS=""
                ;;
        esac
    }
    if [ -n "$BASH" ]; then
        _luamb() {
            local cur prev
            cur="${COMP_WORDS[COMP_CWORD]}"
            prev="${COMP_WORDS[COMP_CWORD-1]}"
            __luamb_completion "$prev"
            # shellcheck disable=SC2207
            COMPREPLY=($(compgen -W "${COMPLETION_OPTS}" -- "${cur}"))
        }
        complete -F _luamb luamb
    elif [ -n "$ZSH_VERSION" ]; then
        _luamb() {
            local words prev
            # shellcheck disable=SC2162
            read -cA words
            prev="${words[-2]}"
            __luamb_completion "$prev"
            # shellcheck disable=SC2034,SC2206
            reply=(${=COMPLETION_OPTS})
        }
        compctl -K _luamb luamb
    fi
fi

return

# """

# shellcheck disable=SC1068,SC2034,SC2125
shellsrc = __doc__[3:]
