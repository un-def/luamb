from __future__ import print_function

import os
import re
import sys
import shutil
import argparse
from importlib import import_module
from collections import OrderedDict
if sys.version_info[0] == 2:
    from StringIO import StringIO
else:
    from io import StringIO


__author__ = 'un.def <un.def@ya.ru>'
__version__ = '0.2.1'


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
                cmd_str = '{0: <6}(aliases: {1})'.format(
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

    re_lua = re.compile('(?P<prefix>(?:lua)?(?P<jit>jit)?)(?P<version>.+)')
    re_rocks = re.compile('(?:lua)?(?:rocks)?(.+)')
    re_env_name = re.compile('^[^/\*?]+$')

    cmd = CMD()

    def __init__(self, env_dir, active_env=None,
                 lua_default=None, luarocks_default=None,
                 hererocks=None):
        self.env_dir = env_dir
        self.active_env = active_env
        self.lua_default = lua_default
        self.luarocks_default = luarocks_default
        self.hererocks = hererocks or import_module('hererocks')
        self.supported_versions = {
            self.TYPE_RIO: self._fetch_supported_versions(
                self.hererocks.RioLua),
            self.TYPE_JIT: self._fetch_supported_versions(
                self.hererocks.LuaJIT),
            'rocks': self._fetch_supported_versions(
                self.hererocks.LuaRocks),
        }
        self.stdout = sys.stdout
        self.stderr = sys.stderr

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
        parser.add_argument(
            '-v', '--version',
            action='version',
            version='luamb ' + __version__,
            help="show luamb version number and exit",
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
            add_help=False,
        )
        parser.add_argument(
            'env_name',
            nargs='?',
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
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=self.hererocks.hererocks_version,
            help="show hererocks version number and exit",
        )
        parser.add_argument(
            '-h', '--help',
            action='store_true',
        )
        args, extra_args = parser.parse_known_args(argv)

        if not args.env_name or args.help:
            _, capture = self._call_hererocks(['--help'], capture_output=True)
            _, _, hererocks_help = capture.partition("optional arguments:\n")
            print("""usage: luamb mk [-a PROJECT_DIR] HEREROCKS_ARGS ENV_NAME

this command is a tiny wrapper around hererocks tool
you can use any hererocks arguments (see below), but instead of a full path
to new environment you should specify only its name
in addition, you can specify a project path with -a/--associate argument
""")
            print(hererocks_help)
            return

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
            '--lua' if lua_type == self.TYPE_RIO else '--luajit',
            lua_version,
        ]
        if rocks_version:
            hererocks_args.extend(['--luarocks', rocks_version])
        hererocks_args.extend(extra_args)
        hererocks_args.append(env_path)

        try:
            self._call_hererocks(hererocks_args)
        except Exception as exc:
            exc_type = exc.__class__.__name__
            raise LuambException(
                "error while running hererocks: {}\n{}".format(exc_type, exc))

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
        env_path = self._get_env_path(env_name)
        try:
            shutil.rmtree(env_path)
        except OSError:
            raise LuambException("can't delete {}".format(env_path))
        print("env '{}' has been deleted".format(env_name))

    @cmd.add('info', 'show')
    def cmd_info(self, argv):
        """show environment info
        """
        if '-h' in argv or '--help' in argv:
            print("usage: luamb info [ENV_NAME]")
            return
        env_name = argv[0] if argv else self.active_env
        if not env_name:
            raise LuambException("no active environment found - "
                                 "specify environment name")
        self._show_env_info(env_name, mark_active=False)

    @cmd.add('ls', 'list')
    def cmd_ls(self, argv):
        """list available environments
        """
        envs = next(os.walk(self.env_dir))[1]
        envs.sort()
        for env in envs:
            self._show_env_info(env)
            print('\n')

    def _call_hererocks(self, argv, capture_output=False):
        if capture_output:
            string_buffer = StringIO()
            sys.stdout = sys.stderr = string_buffer
        exit_status = None
        try:
            self.hererocks.main(argv=argv)
        except SystemExit as e:
            exit_status = e.code
        if capture_output:
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            output = string_buffer.getvalue()
            string_buffer.close()
            return exit_status, output
        return exit_status

    def _show_main_help(self):
        self._show_main_usage()
        print("\navailable commands:\n")
        print(self.cmd.render_help())

    def _get_env_path(self, env_name, raise_exc=True):
        env_path = os.path.join(self.env_dir, env_name)
        if os.path.isdir(env_path):
            return env_path
        if raise_exc:
            raise LuambException("environment '{}' doesn't exist".format(
                                 env_name))

    def _show_env_info(self, env_name, mark_active=True, raise_exc=True):
        env_path = self._get_env_path(env_name, raise_exc=raise_exc)
        if not env_path:
            return
        if mark_active and env_name == self.active_env:
            env_name = '(' + env_name + ')'
        print(env_name)
        print('=' * len(env_name))
        self._call_hererocks(['--show', env_path])
        project_file_path = os.path.join(env_path, '.project')
        if os.path.isfile(project_file_path):
            with open(project_file_path) as f:
                print('Project:', f.read().strip())

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

        groupdict = self.re_lua.match(version_string).groupdict()
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
        version = self.re_rocks.match(version_string).group(1)
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
        hererocks=hererocks,
    )

    try:
        luamb.run()
    except LuambException as exc:
        error(exc)
