# shellcheck shell=bash

# This file is both valid Shell script and Python module.
#
# It can be sourced in shell:
# $ source _shell.py
#
# And it can be imported in Python:
# $ python -c 'import _shell; print(_shell.shellsrc)'

"""":

__luamb_check_exists() {
    type "$@" > /dev/null 2>&1
    return $?
}


__luamb_is_active() {
    __luamb_check_exists deactivate-lua
    return $?
}


__luamb_unset_deactivate_function() {
    unset -f deactivate-lua >/dev/null 2>&1
}


__luamb_wrap_deactivate_function() {
    local __luamb_orig_deactivate_code
    __luamb_orig_deactivate_code=$(typeset -f deactivate-lua | \
        sed 's/deactivate-lua/__luamb_orig_deactivate/g')
    __luamb_unset_deactivate_function
    eval "$__luamb_orig_deactivate_code"
    deactivate-lua() {
        __luamb_off
    }
}


__luamb_on() {
    # tricky way to prevent slashes in env name
    ENV_NAME=$(basename "$1")
    ENV_PATH=$($__luamb_readlink -e "$LUAMB_DIR/$ENV_NAME")
    if [ ! -d "$ENV_PATH" ]; then
        echo "environment doesn't exist: $ENV_NAME"
        return 1
    fi
    if __luamb_is_active; then
        deactivate-lua
    fi
    LUAMB_ORIG_PS1=$PS1
    PS1="($ENV_NAME) $LUAMB_ORIG_PS1"
    LUAMB_ACTIVE_ENV=$ENV_NAME
    __luamb_unset_deactivate_function
    # shellcheck disable=SC1090
    source "$ENV_PATH/bin/activate"
    __luamb_wrap_deactivate_function
    if [ -f "$ENV_PATH/.project" ]; then
        # shellcheck disable=SC2164
        cd "$(cat "$ENV_PATH/.project")"
    fi
    echo "environment activated: $ENV_NAME"
}


__luamb_off() {
    if __luamb_is_active; then
        __luamb_orig_deactivate
        __luamb_unset_deactivate_function
        echo "environment deactivated: $LUAMB_ACTIVE_ENV"
        PS1=$LUAMB_ORIG_PS1
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
