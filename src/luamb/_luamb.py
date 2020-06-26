# coding: utf-8
from __future__ import print_function, unicode_literals

import argparse
import contextlib
import os
import re
import shutil
import sys
from collections import OrderedDict
from importlib import import_module

from luamb.version import __version__

if sys.version_info[0] == 2:
    from StringIO import StringIO
else:
    from io import StringIO


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
                cmd_str = '{0: <38}{1}'.format(cmd_str, cmd_info['desc'])
            help_list.append(cmd_str)
        return '\n'.join(help_list)


class LuambException(Exception):

    message = None

    def __init__(self, message=None):
        if message:
            self.message = message

    def __str__(self):
        return self.message or self.__class__.__name__


class CommandIsShellFunction(LuambException):

    message = (
        "this command is implemented as a shell function "
        "and cannot be called via Python script entrypoint"
    )


class HererocksErrorExit(LuambException):

    status = None

    def __init__(self, system_exit_exc):
        arg = system_exit_exc.args[0]
        if isinstance(arg, int):
            self.status = arg
            self.message = None
        else:
            self.status = 1
            self.message = arg

    def __str__(self):
        msg = 'hererocks exited with non-zero status: {}'.format(self.status)
        if self.message:
            msg = '{}\n{}'.format(msg, self.message)
        return msg


class HererocksUncaughtException(LuambException):

    exc = None

    def __init__(self, exc):
        self.exc = exc
        if exc.args:
            self.message = str(exc)

    def __str__(self):
        msg = 'uncaught exception while running hererocks: {}'.format(
            self.exc.__class__.__name__)
        if self.message:
            msg = '{}\n{}'.format(msg, self.message)
        return msg


class Luamb(object):

    lua_types = ('lua', 'luajit', 'moonjit', 'raptorjit')

    product_cli_args = {
        'lua': ('-l', '--lua'),
        'luajit': ('-j', '--luajit'),
        'moonjit': ('-m', '--moonjit'),
        'raptorjit': ('--raptorjit',),
        'luarocks': ('-r', '--luarocks'),
    }
    product_hererocks_classes = {
        'lua': 'RioLua',
        'luajit': 'LuaJIT',
        'moonjit': 'MoonJIT',
        'raptorjit': 'RaptorJIT',
        'luarocks': 'LuaRocks',
    }
    product_names = {
        'lua': 'PUC-Rio Lua',
        'luajit': 'LuaJIT',
        'moonjit': 'moonjit',
        'raptorjit': 'RaptorJIT',
        'luarocks': 'LuaRocks',
    }

    re_env_name = re.compile(r'^[^/\*?]+$')

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
            product_key: self._fetch_supported_versions(cls_name)
            for product_key, cls_name in self.product_hererocks_classes.items()
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

    @cmd.add('on', 'enable', 'activate')
    def cmd_on(self, argv):
        """activate environment"""
        raise CommandIsShellFunction

    @cmd.add('off', 'disable', 'deactivate')
    def cmd_off(self, argv):
        """deactivate environment"""
        raise CommandIsShellFunction

    @cmd.add('mk', 'new', 'create')
    def cmd_mk(self, argv):
        """create new environment"""
        parser = argparse.ArgumentParser(
            prog='luamb mk',
            add_help=False,
            description="""
                This command is a tiny wrapper around hererocks tool.
                You can use any hererocks arguments (see below), but instead of
                a full path to new environment you should specify only
                its name. In addition, you can specify a project path with
                -a/--associate argument.
            """,
            usage=(
                '\n  luamb mk [-a PROJECT_DIR] [--no-luarocks] HEREROCKS_ARGS '
                'ENV_NAME\n'
                '  luamb mk --list-versions WHAT'
            ),
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
            '--no-luarocks',
            action='store_true',
            help="don't install LuaRocks (if default version specified via "
                 "environment variable)",
        )
        parser.add_argument(
            '--list-versions',
            choices=self.product_names,
            metavar='WHAT',
            help=(
                'list versions of Lua interpreter or LuaRocks '
                '(one of %(choices)s) available for installation'
            ),
        )
        for product_key, product_cli_args in self.product_cli_args.items():
            parser.add_argument(
                *product_cli_args,
                dest=product_key,
                help=argparse.SUPPRESS
            )
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=self.hererocks.hererocks_version,
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            '-h', '--help',
            action='store_true',
            help=argparse.SUPPRESS,
        )
        args, extra_args = parser.parse_known_args(argv)

        if args.help or (not args.env_name and not args.list_versions):
            output = self._call_hererocks(['--help'], capture_output=True)
            hererocks_help = output.partition("optional arguments:\n")[2]
            parser.print_help()
            print('\nhererocks arguments:')
            print(hererocks_help)
            return

        if args.list_versions:
            product_key = args.list_versions
            versions = self._get_supported_versions(product_key)
            print('Supported {} versions are: {}'.format(
                self.product_names[product_key],
                self._format_versions_string(versions),
            ))
            print('latest and ^ are aliases for {}'.format(versions['latest']))
            return

        env_name = args.env_name
        if not self.re_env_name.match(env_name):
            raise LuambException("invalid env name: '{}'".format(env_name))

        args_lua_types = []
        for lua_type in self.lua_types:
            lua_version = getattr(args, lua_type)
            if lua_version is not None:
                args_lua_types.append((lua_type, lua_version))

        if len(args_lua_types) > 1:
            raise LuambException("can't install more than one Lua interpreter")

        if len(args_lua_types) == 1:
            lua_type, lua_version = args_lua_types[0]
        else:
            if not self.lua_default:
                raise LuambException(
                    "specify Lua version argument "
                    "or set default version via environment variable"
                )
            print(
                "Lua version argument is not specified, use the default value "
                "from enviroment variable"
            )
            lua_type, _, lua_version = self.lua_default.strip().partition(' ')
            lua_type = lua_type.rstrip()
            lua_version = lua_version.lstrip()
            if not lua_type or not lua_version:
                raise LuambException(
                    "Error parsing Lua version "
                    "environment variable: {}".format(self.lua_default)
                )

        self._check_product_version_is_supported(lua_type, lua_version)

        if args.no_luarocks:
            luarocks_version = None
        elif args.luarocks is not None:
            luarocks_version = args.luarocks
        elif self.luarocks_default:
            print(
                "LuaRocks version argument is not specified, "
                "use the default value from enviroment variable"
            )
            luarocks_version = self.luarocks_default.strip()
        else:
            luarocks_version = None

        if luarocks_version is not None:
            self._check_product_version_is_supported(
                'luarocks', luarocks_version)

        env_path = os.path.join(self.env_dir, env_name)

        hererocks_args = [
            self.product_cli_args[lua_type][-1],
            lua_version,
        ]
        if luarocks_version:
            hererocks_args.extend([
                self.product_cli_args['luarocks'][-1],
                luarocks_version,
            ])
        hererocks_args.extend(extra_args)
        hererocks_args.append(env_path)
        self._call_hererocks(hererocks_args)

        if args.associate:
            with open(os.path.join(env_path, '.project'), 'w') as f:
                f.write(os.path.abspath(os.path.expandvars(args.associate)))

    @cmd.add('rm', 'remove', 'del', 'delete')
    def cmd_rm(self, argv):
        """remove environment"""
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
        """show environment info"""
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
        """list available environments"""
        parser = argparse.ArgumentParser(prog='luamb ls')
        parser.add_argument(
            '-s', '--short',
            action='store_true',
            help="show only names of environments",
        )
        args = parser.parse_args(argv)
        envs = next(os.walk(self.env_dir))[1]
        envs.sort()
        detail = not args.short
        for env in envs:
            self._show_env_info(env, detail=detail)
            if detail:
                print('\n')

    @contextlib.contextmanager
    def _maybe_capture_output(self, capture_output):
        string_buffer = StringIO()
        if capture_output:
            stdout, stderr = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = string_buffer
        try:
            yield string_buffer
        finally:
            if capture_output:
                sys.stdout, sys.stderr = stdout, stderr
            string_buffer.close()

    def _call_hererocks(self, argv, capture_output=False):
        with self._maybe_capture_output(capture_output) as output_buffer:
            try:
                self.hererocks.main(argv=argv)
            except SystemExit as exc:
                if exc.code:
                    raise HererocksErrorExit(exc)
            except Exception as exc:
                raise HererocksUncaughtException(exc)
            if capture_output:
                return output_buffer.getvalue()

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

    def _show_env_info(
        self, env_name, detail=True, mark_active=True, raise_exc=True,
    ):
        env_path = self._get_env_path(env_name, raise_exc=raise_exc)
        if not env_path:
            return
        if mark_active and env_name == self.active_env:
            env_name = '(' + env_name + ')'
        print(env_name)
        if not detail:
            return
        print('=' * len(env_name))
        self._call_hererocks(['--show', env_path])
        project_file_path = os.path.join(env_path, '.project')
        if os.path.isfile(project_file_path):
            with open(project_file_path) as f:
                print('Project:', f.read().strip())

    def _fetch_supported_versions(self, hererocks_cls_name):
        try:
            cls = getattr(self.hererocks, hererocks_cls_name)
        except AttributeError:
            return {}
        versions = {v: v for v in cls.versions}
        versions.update(cls.translations)
        return versions

    def _get_supported_versions(self, product_key, raise_exc=True):
        versions = self.supported_versions[product_key]
        if versions or not raise_exc:
            return versions
        raise LuambException(
            '{} is not supported\n'
            'Try to upgrade hererocks'.format(self.product_names[product_key])
        )

    def _format_versions_string(self, versions):
        return '  '.join(sorted(versions))

    def _check_product_version_is_supported(self, product_key, version):
        if product_key != 'luarocks' and product_key not in self.lua_types:
            raise LuambException(
                'Unsupported Lua interpreter: {}'.format(product_key)
            )
        product_name = self.product_names[product_key]
        if not version:
            raise LuambException(
                '{} version is not specified'.format(product_name))
        if self._is_local_path_or_git_uri(version):
            return
        supported_versions = self._get_supported_versions(product_key)
        if version not in supported_versions:
            raise LuambException(
                'Unsupported {} version: {}\n'
                'Supported versions are: {}'.format(
                    product_name,
                    version,
                    self._format_versions_string(supported_versions),
                )
            )

    def _is_local_path_or_git_uri(self, version_string, skip_path_check=False):
        if '@' in version_string:
            return True
        if (
                not version_string.startswith('/')
                and not version_string.startswith('./')
                and not version_string.startswith('../')
        ):
            return False
        if skip_path_check:
            return True
        if not os.path.exists(version_string):
            raise LuambException(
                "'{}' seems like local path "
                "but doesn't exist".format(version_string)
            )
        if not os.path.isdir(version_string):
            raise LuambException(
                "'{}' is not a directory ".format(version_string)
            )
        return True
