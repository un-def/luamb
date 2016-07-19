from __future__ import print_function

import sys
import os
import re
import argparse
import subprocess
from importlib import import_module
from collections import OrderedDict


def error(msg, exit_status=1):
    print(msg)
    sys.exit(exit_status)


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
                cmd_str = '{0: <4}(aliases: {1})'.format(
                    cmd_str, ', '.join(cmd_info['aliases']))
            if cmd_info['desc']:
                cmd_str = '{0: <30}{1}'.format(cmd_str, cmd_info['desc'])
            help_list.append(cmd_str)
        return '\n'.join(help_list)


class Luamb(object):

    TYPE_RIO = 1
    TYPE_JIT = 2
    TYPE_ALL = TYPE_RIO | TYPE_JIT

    re_lua = re.compile('Lua(?:JIT)? [0-9.]+')
    re_rocks = re.compile('LuaRocks [0-9.]+')
    re_ver = re.compile('(?P<prefix>(?:lua)?(?P<jit>jit)?)(?P<version>.+)')

    usage = "luamb COMMAND [ARGS]"

    cmd = CMD()

    def __init__(self, env_dir, lua_default=None, hererocks_module=None):
        self.env_dir = env_dir
        self.lua_default = lua_default
        self.hererocks_module = hererocks_module or import_module('hererocks')
        self.supported_versions = {
            'PUC-Rio Lua': self._get_supported_versions(
                self.hererocks_module.RioLua),
            'LuaJIT': self._get_supported_versions(
                self.hererocks_module.LuaJIT),
            'LuaRocks': self._get_supported_versions(
                self.hererocks_module.LuaRocks),
        }

    def run(self, argv):
        parser = argparse.ArgumentParser(
            prog='luamb',
            description="luamb - Lua virtual environment",
            usage=self.usage,
            add_help=False,
        )
        parser.add_argument(
            'command',
            nargs='?',
            default='',
        )
        parser.add_argument(
            '-h', '--help',
            action='store_true',
        )
        args = parser.parse_args(argv[1:2])
        self.print_usage = parser.print_usage
        if not args.command or args.help:
            self.show_help()
            return
        method = self.cmd.resolve(args.command)
        if not method:
            print("command '{}' not found\n"
                  "try 'luamb --help'".format(args.command))
        else:
            method(self, argv[2:])

    @cmd.add('on', 'enable')
    def cmd_on(self, argv):
        """activate environment
        """

    @cmd.add('off', 'disable')
    def cmd_off(self, argv):
        """deactivate environment
        """

    @cmd.add('mk', 'new', 'create')
    def cmd_mk(self, argv):
        """create new environment
        """

    @cmd.add('rm', 'remove', 'del')
    def cmd_rm(self, argv):
        """remove environment
        """

    @cmd.add('ls', 'list')
    def cmd_ls(self, argv):
        """list available environments
        """
        envs = next(os.walk(self.env_dir))[1]
        envs.sort()
        for env in envs:
            env_path = os.path.join(self.env_dir, env)
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

    def show_help(self):
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

    def _get_supported_versions(self, lua_cls):
        versions = {v: v for v in lua_cls.versions}
        versions.update(lua_cls.translations)
        return versions

    def _normalize_lua_version(self, version_string, lua_type=None):
        version_string = version_string.lower()
        if not lua_type:
            lua_type = self.TYPE_ALL

        groupdict = self.re_ver.match(version_string).groupdict()
        prefix = bool(groupdict['prefix'])
        jit = bool(groupdict['jit'])
        version = groupdict['version']

        if lua_type == self.TYPE_ALL and not prefix:
            raise ValueError("specify implementation (PUC-Rio Lua or LuaJIT)")
        if lua_type == self.TYPE_RIO and jit:
            raise ValueError("specify PUC-Rio Lua version, not LuaJIT")
        if lua_type == self.TYPE_JIT and prefix and not jit:
            raise ValueError("specify LuaJIT version, not PUC-Rio")

        if lua_type == self.TYPE_ALL:
            lua_type = self.TYPE_JIT if jit else self.TYPE_RIO

        impl = 'LuaJIT' if lua_type == self.TYPE_JIT else 'PUC-Rio Lua'

        try:
            norm_version = self.supported_versions[impl][version]
        except KeyError:
            raise ValueError("non supported {} version: {}".format(
                impl, version))

        return lua_type, norm_version


if __name__ == '__main__':

    try:
        import hererocks
    except ImportError:
        error("'hererocks' is not installed")

    luamb_dir = os.environ.get('LUAMB_DIR')
    if not luamb_dir:
        error("LUAMB_DIR variable is not set")

    luamb_dir = os.path.abspath(luamb_dir)
    if not os.path.isdir(luamb_dir):
        error("LUAMB_DIR='{}' is not a directory".format(luamb_dir))

    luamb_lua_default = os.environ.get('LUAMB_LUA_DEFAULT')

    Luamb(
        env_dir=luamb_dir,
        lua_default=luamb_lua_default,
        hererocks_module=hererocks,
    ).run(sys.argv)
