LUAMB_ORIG_PS1=$PS1
LUAMB_PYTHON_BIN=${LUAMB_PYTHON_BIN:-'/usr/bin/env python'}


luamb_is_active() {
    type deactivate-lua > /dev/null 2>&1
    return $?
}


luamb_on() {
    ENV_NAME=$(basename $1)   # tricky way to prevent slashes in env name
    ENV_PATH=$(readlink -f "$LUAMB_DIR/$ENV_NAME")
    if [ ! -d "$ENV_PATH" ]
    then
        echo "environment $ENV_PATH doesn't exist"
        return 1
    fi
    if luamb_is_active
    then
        deactivate-lua
    fi
    PS1="($ENV_NAME) $LUAMB_ORIG_PS1"
    source "$ENV_PATH/bin/activate"
    echo "environment activated: $ENV_NAME"
}


luamb_off() {
    PS1=$LUAMB_ORIG_PS1
    if luamb_is_active
    then
        deactivate-lua
        echo "environment deactivated"
    else
        echo "no active environment"
    fi
}


luamb_cmd() {
    # set LUAMB_SCRIPT_PATH=/path/to/luamb.py in development mode
    if [ -z "$LUAMB_SCRIPT_PATH" ]
    then
        $LUAMB_PYTHON_BIN -m luamb "$@"
    else
        $LUAMB_PYTHON_BIN $LUAMB_SCRIPT_PATH "$@"
    fi
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
            luamb_on $2
            ;;
        "off"|"disable")
            luamb_off
            ;;
        *)
            luamb_cmd "$@"
    esac
}
