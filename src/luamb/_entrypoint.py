from __future__ import print_function

import os
import sys


def main():
    # This part should execute as fast as possible so as not to slow down
    # shell startup. For this reason we do not use ArgumentParser here and
    # do not import anything on module level except for some standard modules.
    if len(sys.argv) == 2 and sys.argv[1] == 'shellsrc':
        from luamb._shell import shellsrc
        print(shellsrc)
        sys.exit()

    from luamb._luamb import Luamb, LuambException

    def error(msg, exit_status=1):
        msg = '\033[0;31m{}\033[0m'.format(msg)
        print(msg, file=sys.stderr)
        sys.exit(exit_status)

    try:
        import hererocks
    except ImportError:
        error("'hererocks' is not installed")

    luamb_dir = os.environ.get('LUAMB_DIR')
    if not luamb_dir:
        error("LUAMB_DIR variable is not set")

    luamb_dir = os.path.expandvars(luamb_dir)
    if not os.path.isdir(luamb_dir):
        error("LUAMB_DIR='{}' is not a directory".format(luamb_dir))

    luamb = Luamb(
        env_dir=luamb_dir,
        active_env=os.environ.get('LUAMB_ACTIVE_ENV'),
        lua_default=os.environ.get('LUAMB_LUA_DEFAULT'),
        luarocks_default=os.environ.get('LUAMB_LUAROCKS_DEFAULT'),
        hererocks=hererocks,
    )

    try:
        luamb.run()
    except LuambException as exc:
        error(exc)
