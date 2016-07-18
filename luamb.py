from __future__ import print_function

import sys
import os
import re
import argparse
import subprocess
from collections import OrderedDict


def error(msg, exit_status=1):
    print(msg)
    sys.exit(exit_status)


try:
    import hererocks
except ImportError:
    error("'hererocks' is not installed")


class CMD(object):

    def __init__(self):
        self.registry = OrderedDict()

    def add(self, *aliases):
        def decorator(func):
            cmd_info = {
                'cmd': aliases[0],
                'callable': func,
                'desc': (func.__doc__ or '').rstrip(),
                'aliases': aliases[1:],
            }
            for alias in aliases:
                self.registry[alias] = cmd_info
            return func
        return decorator

    def resolve(self, cmd):
        if cmd in self.registry:
            return self.registry[cmd]['callable']

    def render_help(self):
        help_list = []
        for cmd, cmd_info in self.registry.items():
            if cmd != cmd_info['cmd']:
                continue
            cmd_str = cmd
            if cmd_info['aliases']:
                cmd_str = '{0} (aliases: {1})'.format(
                    cmd_str, ', '.join(cmd_info['aliases']))
            if cmd_info['desc']:
                cmd_str = '{0: <30}{1}'.format(cmd_str, cmd_info['desc'])
            help_list.append(cmd_str)
        return '\n'.join(help_list)


class Luamb(object):

    cmd = CMD()
    re_lua = re.compile('Lua(?:JIT)? [0-9.]+')
    re_rocks = re.compile('LuaRocks [0-9.]+')
    usage = "luamb COMMAND [ARGS]"

    def __init__(self, luamb_dir, argv):
        self.luamb_dir = luamb_dir
        parser = argparse.ArgumentParser(
            prog='luamb',
            description="luamb - Lua virtual environment",
            usage=self.usage,
            add_help=False,
        )
        parser.add_argument(
            'command',
            nargs='?',
            default='help',
        )
        parser.add_argument(
            '-h', '--help',
            action='store_true',
        )
        args = parser.parse_args(argv[1:2])
        self.print_usage = parser.print_usage
        if args.help:
            self.cmd_help()
            return
        method = self.cmd.resolve(args.command)
        if not method:
            print("command '{}' not found\n"
                  "try 'luamb help'".format(args.command))
        else:
            method(self, argv[2:])

    @cmd.add('new', 'create', 'add')
    def cmd_new(self, argv):
        """create new environment
        """

    @cmd.add('remove', 'rm', 'del')
    def cmd_remove(self):
        """remove environment
        """

    @cmd.add('list', 'ls')
    def cmd_list(self, argv):
        """list available environments
        """
        envs = next(os.walk(self.luamb_dir))[1]
        envs.sort()
        for env in envs:
            env_path = os.path.join(self.luamb_dir, env)
            print(env)
            print('='*len(env))
            print(env_path)
            lua_bin = os.path.join(env_path, 'bin', 'lua')
            ok, output = self._get_output([lua_bin, '-v'], regex=self.re_lua)
            if ok:
                print(output)
            else:
                print('Lua -', output)
            luarocks_bin = os.path.join(env_path, 'bin', 'luarocks')
            ok, output = self._get_output([luarocks_bin], regex=self.re_rocks)
            if ok:
                print(output)
            else:
                print('LuaRocks -', output)
            print()

    @cmd.add('help')
    def cmd_help(self, argv=None):
        """print help message
        """
        self.print_usage()
        print("\navailable commands:\n")
        print(self.cmd.render_help())

    def _get_output(self, args, regex=None):
        try:
            output = subprocess.check_output(args).decode('utf-8').strip()
        except OSError:
            return False, "executable not found"
        except subprocess.CalledProcessError:
            return False, "error while running executable"
        if not regex:
            return True, output
        mo = regex.search(output)
        if mo:
            return True, mo.group(0)
        return False, "error parsing version"

    def _make_version_dict(self, lua_cls):
        versions = {v: None for v in lua_cls.versions}
        versions.update(lua_cls.translations)
        return versions


if __name__ == '__main__':

    luamb_dir = os.environ.get('LUAMB_DIR')
    if not luamb_dir:
        error("LUAMB_DIR variable is not set")

    luamb_dir = os.path.abspath(luamb_dir)
    if not os.path.isdir(luamb_dir):
        error("LUAMB_DIR='{}' is not a directory".format(luamb_dir))

    Luamb(luamb_dir=luamb_dir, argv=sys.argv)
