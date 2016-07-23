# author  : un.def <un.def@ya.ru>
# version : 0.1.1

if [ -z "$LUAMB_DIR" ]
then
  echo "LUAMB_DIR variable not set"
  return 1
fi

export LUAMB_ACTIVE_ENV=""
LUAMB_ORIG_PS1=$PS1
LUAMB_PYTHON_BIN=${LUAMB_PYTHON_BIN:-'/usr/bin/env python'}

if [ "$LUAMB_COMPLETION" = "true" ]
then
    complete -F _luamb luamb
fi


__luamb_is_active() {
    type deactivate-lua > /dev/null 2>&1
    return $?
}


__luamb_on() {
    ENV_NAME=$(basename $1)   # tricky way to prevent slashes in env name
    ENV_PATH=$(readlink -f "$LUAMB_DIR/$ENV_NAME")
    if [ ! -d "$ENV_PATH" ]
    then
        echo "environment $ENV_PATH doesn't exist"
        return 1
    fi
    if __luamb_is_active
    then
        deactivate-lua
    fi
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
    PS1=$LUAMB_ORIG_PS1
    LUAMB_ACTIVE_ENV=""
    if __luamb_is_active
    then
        deactivate-lua
        echo "environment deactivated"
    else
        echo "no active environment"
    fi
}


__luamb_cmd() {
    # set LUAMB_SCRIPT_PATH=/path/to/luamb.py in development mode
    if [ -z "$LUAMB_SCRIPT_PATH" ]
    then
        CMD="$LUAMB_PYTHON_BIN -m luamb $@"
    else
        CMD="$LUAMB_PYTHON_BIN $LUAMB_SCRIPT_PATH $@"
    fi
    $CMD
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
            __luamb_on $2
            ;;
        "off"|"disable")
            __luamb_off
            ;;
        *)
            __luamb_cmd "$@"
    esac
}


_luamb() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    case $prev in
        "luamb")
            opts="on enable off disable mk new create \
                  rm remove del ls list --help"
            ;;
        "on"|"enable")
            opts=$(find "$LUAMB_DIR" -mindepth 1 -maxdepth 1 \
                   -type d -printf "%f ")
            ;;
        *)
            return 0
            ;;
    esac
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}
