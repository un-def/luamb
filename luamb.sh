# author  : un.def <un.def@ya.ru>
# version : 0.2.1


__luamb_check_exists() {
  type "$@" > /dev/null 2>&1
  return $?
}


__luamb_is_active() {
    __luamb_check_exists deactivate-lua
    return $?
}


__luamb_on() {
    ENV_NAME=$(basename "$1")   # tricky way to prevent slashes in env name
    ENV_PATH=$($READLINK -e "$LUAMB_DIR/$ENV_NAME")
    if [ ! -d "$ENV_PATH" ]
    then
        echo "environment doesn't exist: $ENV_NAME"
        return 1
    fi
    if __luamb_is_active
    then
        deactivate-lua
    fi
    LUAMB_ORIG_PS1=$PS1
    PS1="($ENV_NAME) $LUAMB_ORIG_PS1"
    LUAMB_ACTIVE_ENV=$ENV_NAME
    source "$ENV_PATH/bin/activate"
    if [ -f "$ENV_PATH/.project" ]
    then
      cd $(cat "$ENV_PATH/.project")
    fi
    echo "environment activated: $ENV_NAME"
}


__luamb_off() {
    if __luamb_is_active
    then
        deactivate-lua
        echo "environment deactivated: $LUAMB_ACTIVE_ENV"
        PS1=$LUAMB_ORIG_PS1
        LUAMB_ACTIVE_ENV=""
    else
        echo "no active environment"
    fi
}


__luamb_cmd() {
    # set LUAMB_SCRIPT_PATH=/path/to/luamb.py in development mode
    if [ -z "$LUAMB_SCRIPT_PATH" ]
    then
        CMD=("$LUAMB_PYTHON_BIN" -m luamb "$@")
    else
        CMD=("$LUAMB_PYTHON_BIN" "$LUAMB_SCRIPT_PATH" "$@")
    fi
    "${CMD[@]}"
    return $?
}


luamb() {
    case "$1" in
        "on"|"enable")
            if [ -z "$2" ]
            then
                echo "usage: luamb on ENV_NAME"
                return 1
            fi
            __luamb_on "$2"
            ;;
        "off"|"disable")
            __luamb_off
            ;;
        *)
            __luamb_cmd "$@"
    esac
}


if [ -z "$LUAMB_DIR" ]
then
  echo "LUAMB_DIR variable not set"
  return 1
fi

if [ "$(uname)" = "Darwin" ]
then
  READLINK="greadlink"
  if ! __luamb_check_exists $READLINK
  then
    echo "luamb: greadlink not found, install coreutils:"
    echo "brew install coreutils"
    return 1
  fi
else
  READLINK="readlink"
fi

export LUAMB_ACTIVE_ENV=""
LUAMB_PYTHON_BIN=${LUAMB_PYTHON_BIN:-$(/usr/bin/which python)}

if [ "$LUAMB_COMPLETION" = "true" ]
then
    __luamb_completion() {
        case "$1" in
            luamb)
                COMPLETION_OPTS="on enable off disable mk new create \
                                 rm remove del info show ls list"
                ;;
            on|enable|rm|remove|del|info|show)
                COMPLETION_OPTS=$(find "$LUAMB_DIR" -mindepth 1 -maxdepth 1 \
                                  -type d -printf "%f ")
                ;;
            *)
                COMPLETION_OPTS=""
                ;;
        esac
    }
    if [ -n "$BASH" ]
    then
        _luamb() {
            local cur prev
            cur="${COMP_WORDS[COMP_CWORD]}"
            prev="${COMP_WORDS[COMP_CWORD-1]}"
            __luamb_completion "$prev"
            COMPREPLY=($(compgen -W "${COMPLETION_OPTS}" -- ${cur}))
        }
        complete -F _luamb luamb
    elif [ -n "$ZSH_VERSION" ]
    then
        _luamb() {
            local words prev
            read -cA words
            prev="${words[-2]}"
            __luamb_completion "$prev"
            reply=(${=COMPLETION_OPTS})
        }
        compctl -K _luamb luamb
    fi
fi
