LUAMB_ORIG_PS1=$PS1


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


luamb() {
    if [ $# -eq 0 ]
    then
        $LUAMB_BIN
        return
    fi
    case "$1" in
        "on")
            if [ -z "$2" ]
            then
                echo "usage: luamb on ENV_NAME"
                return 1
            fi
            luamb_on $2
            ;;
        "off")
            luamb_off
            ;;
        *)
            $LUAMB_BIN "$@"
    esac
}
