from __future__ import print_function

import os
import re
import sys
import shutil
import argparse
import subprocess
from importlib import import_module
from collections import OrderedDict


__author__ = 'un.def <un.def@ya.ru>'
__version__ = '0.1.0'


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


class LuambException(Exception):

    pass


class Luamb(object):

    TYPE_RIO = 1
    TYPE_JIT = 2
    TYPE_ALL = TYPE_RIO | TYPE_JIT

    implementations = {
        TYPE_RIO: 'PUC-Rio Lua',
        TYPE_JIT: 'LuaJIT',
    }

    re_lua = re.compile('Lua(?:JIT)? [0-9.]+')
    re_rocks = re.compile('LuaRocks [0-9.]+')
    re_lua_v = re.compile('(?P<prefix>(?:lua)?(?P<jit>jit)?)(?P<version>.+)')
    re_rocks_s = re.compile('(?:lua)?(?:rocks)?(.+)')
    re_env_name = re.compile('^[^/\*?]+$')

    cmd = CMD()

    def __init__(self, env_dir, active_env=None,
                 lua_default=None, luarocks_default=None,
                 hererocks_module=None):
        self.env_dir = env_dir
        self.active_env = active_env
        self.lua_default = lua_default
        self.luarocks_default = luarocks_default
        self.hererocks_module = hererocks_module or import_module('hererocks')
        self.supported_versions = {
            self.TYPE_RIO: self._fetch_supported_versions(
                self.hererocks_module.RioLua),
            self.TYPE_JIT: self._fetch_supported_versions(
                self.hererocks_module.LuaJIT),
            'rocks': self._fetch_supported_versions(
                self.hererocks_module.LuaRocks),
        }

    def run(self, argv=None):
        if not argv:
            argv = sys.argv[1:]
        parser = argparse.ArgumentParser(
            prog='luamb',
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
        args = parser.parse_args(argv[:1])
        self._show_main_usage = parser.print_usage
        if not args.command or args.help:
            self._show_main_help()
            return
        method = self.cmd.resolve(args.command)
        if not method:
            print("command '{}' not found\n"
                  "try 'luamb --help'".format(args.command))
        else:
            method(self, argv[1:])

    @cmd.add('on', 'enable')
    def cmd_on(self, argv):
        """activate environment
        """
        print("usage: luamb on ENV_NAME\nthis command is implemented "
              "as shell function and can't be called via luamb.py")

    @cmd.add('off', 'disable')
    def cmd_off(self, argv):
        """deactivate environment
        """
        print("usage: luamb off\nthis command is implemented "
              "as shell function and can't be called via luamb.py")

    @cmd.add('mk', 'new', 'create')
    def cmd_mk(self, argv):
        """create new environment
        """
        parser = argparse.ArgumentParser(
            prog='luamb mk',
        )
        parser.add_argument(
            'env_name',
            metavar='ENV_NAME',
            help="environment name (used as directory name)"
        )
        parser.add_argument(
            '-a', '--associate',
            metavar='PROJECT_DIR',
            help="associate env with project",
        )
        parser.add_argument(
            '-l', '--lua',
            help="version of PUC-Rio Lua",
        )
        parser.add_argument(
            '-j', '--luajit',
            help="version of LuaJIT",
        )
        parser.add_argument(
            '-r', '--luarocks',
            help="version of LuaRocks",
        )
        parser.add_argument(
            '-n', '--no-luarocks',
            action='store_true',
            help="don't install LuaRocks (if default version specified via "
                 "environment variable)",
        )
        args, extra_args = parser.parse_known_args(argv)

        env_name = args.env_name
        if not self.re_env_name.match(env_name):
            raise LuambException("invalid env name: '{}'".format(env_name))

        if args.lua and args.luajit:
            raise LuambException("can't install both PUC-Rio Lua and LuaJIT")

        if args.lua or args.luajit:
            lua_type, lua_version = self._normalize_lua_version(
                args.lua or args.luajit,
                self.TYPE_RIO if args.lua else self.TYPE_JIT
            )
        else:
            if not self.lua_default:
                raise LuambException(
                    "specify Lua version with --lua/--luajit argument "
                    "or set default version via environment variable"
                )

            try:
                lua_type, lua_version = self._normalize_lua_version(
                    self.lua_default)
            except LuambException as exc:
                raise LuambException(
                    "Error parsing default Lua version "
                    "environment variable: {}".format(exc)
                )

        if args.luarocks:
            rocks_version = self._normalize_rocks_version(args.luarocks)
        elif not args.no_luarocks and self.luarocks_default:
            try:
                rocks_version = self._normalize_rocks_version(
                    self.luarocks_default)
            except LuambException as exc:
                raise LuambException(
                    "Error parsing default LuaRocks version "
                    "environment variable: {}".format(exc)
                )
        else:
            rocks_version = None

        env_path = os.path.join(self.env_dir, env_name)

        hererocks_args = [
            sys.executable,
            self.hererocks_module.__file__,
            '--lua' if lua_type == self.TYPE_RIO else '--luajit',
            lua_version,
        ]
        if rocks_version:
            hererocks_args.extend(['--luarocks', rocks_version])
        hererocks_args.extend(extra_args)
        hererocks_args.append(env_path)
        try:
            subprocess.check_call(hererocks_args)
        except subprocess.CalledProcessError:
            raise LuambException("error while running hererocks")

        if args.associate:
            with open(os.path.join(env_path, '.project'), 'w') as f:
                f.write(os.path.abspath(os.path.expandvars(args.associate)))

    @cmd.add('rm', 'remove', 'del')
    def cmd_rm(self, argv):
        """remove environment
        """
        if not argv or len(argv) > 1 or '-h' in argv or '--help' in argv:
            print("usage: luamb rm ENV_NAME")
            return
        env_name = argv[0]
        env_path = os.path.join(self.env_dir, env_name)
        if not os.path.isdir(env_path):
            raise LuambException("env '{}' doesn't exist".format(env_name))
        try:
            shutil.rmtree(env_path)
        except OSError:
            raise LuambException("can't delete {}".format(env_path))
        print("env '{}' has been deleted".format(env_name))

    @cmd.add('ls', 'list')
    def cmd_ls(self, argv):
        """list available environments
        """
        envs = next(os.walk(self.env_dir))[1]
        envs.sort()
        for env in envs:
            env_path = os.path.join(self.env_dir, env)
            if env == self.active_env:
                env = '[*] '+env
            print(env)
            print('='*len(env))
            print(env_path)
            lua_bin = os.path.join(env_path, 'bin', 'lua')
            try:
                print(self._get_output([lua_bin, '-v'], regex=self.re_lua))
            except LuambException as exc:
                print('Lua:', exc)
            luarocks_bin = os.path.join(env_path, 'bin', 'luarocks')
            try:
                print(self._get_output([luarocks_bin], regex=self.re_rocks))
            except LuambException as exc:
                print('LuaRocks:', exc)
            project_file_path = os.path.join(env_path, '.project')
            if os.path.isfile(project_file_path):
                with open(project_file_path) as f:
                    project = f.read().strip()
                print('project:', project)
            else:
                print('no associated project')
            print()

    def _show_main_help(self):
        self._show_main_usage()
        print("\navailable commands:\n")
        print(self.cmd.render_help())

    def _get_output(self, args, regex=None):
        try:
            output = subprocess.check_output(
                args, stderr=subprocess.STDOUT).decode('utf-8').strip()
        except OSError:
            raise LuambException("executable not found")
        except subprocess.CalledProcessError:
            raise LuambException("error while running executable")
        if not regex:
            return output
        mo = regex.search(output)
        if mo:
            return mo.group(0)
        raise LuambException("error parsing version")

    def _fetch_supported_versions(self, lua_cls):
        versions = {v: v for v in lua_cls.versions}
        versions.update(lua_cls.translations)
        return versions

    def _get_supported_versions(self, product_key, separator=None):
        versions = list(sorted(self.supported_versions[product_key]))
        if not separator:
            return versions
        return separator.join(versions)

    def _normalize_lua_version(self, version_string, lua_type=None):
        version_string = version_string.lower()
        if not lua_type:
            lua_type = self.TYPE_ALL

        groupdict = self.re_lua_v.match(version_string).groupdict()
        prefix = bool(groupdict['prefix'])
        jit = bool(groupdict['jit'])
        version = groupdict['version']

        if lua_type == self.TYPE_ALL and not prefix:
            raise LuambException(
                "specify implementation (PUC-Rio Lua or LuaJIT)")
        if lua_type == self.TYPE_RIO and jit:
            raise LuambException("specify PUC-Rio Lua version, not LuaJIT")
        if lua_type == self.TYPE_JIT and prefix and not jit:
            raise LuambException("specify LuaJIT version, not PUC-Rio")

        if lua_type == self.TYPE_ALL:
            lua_type = self.TYPE_JIT if jit else self.TYPE_RIO

        try:
            norm_version = self.supported_versions[lua_type][version]
        except KeyError:
            supported_versions = self._get_supported_versions(lua_type, '  ')
            raise LuambException(
                "non-supported {} version: {}\n"
                "supported versions are: {}".format(
                    self.implementations[lua_type],
                    version,
                    supported_versions
                )
            )

        return lua_type, norm_version

    def _normalize_rocks_version(self, version_string):
        version_string = version_string.lower()
        version = self.re_rocks_s.match(version_string).group(1)
        try:
            return self.supported_versions['rocks'][version]
        except KeyError:
            supported_versions = self._get_supported_versions('rocks', '  ')
            raise LuambException(
                "non-supported LuaRocks version: {}\n"
                "supported versions are: {}".format(
                    version,
                    supported_versions
                )
            )

if __name__ == '__main__':

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

    luamb_lua_default = os.environ.get('LUAMB_LUA_DEFAULT')
    luamb_luarocks_default = os.environ.get('LUAMB_LUAROCKS_DEFAULT')
    luamb_active_env = os.environ.get('LUAMB_ACTIVE_ENV')

    luamb = Luamb(
        env_dir=luamb_dir,
        active_env=luamb_active_env,
        lua_default=luamb_lua_default,
        luarocks_default=luamb_luarocks_default,
        hererocks_module=hererocks,
    )

    try:
        luamb.run()
    except LuambException as exc:
        sys.exit(exc)
