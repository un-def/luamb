import inspect
import shlex
import subprocess
import warnings


class ShellWarning(UserWarning):

    pass


class ShellError(Exception):

    def warn(self):
        warnings.warn(str(self), category=ShellWarning)


class Shell(object):

    def __init__(self, name, command):
        self.name = name
        self.configure(command)

    def configure(self, command):
        self._command = tuple(shlex.split(command))
        try:
            del self._available
        except AttributeError:
            pass

    def check(self):
        err = None
        try:
            output = subprocess.check_output(
                self('echo check'), stderr=subprocess.STDOUT).decode('utf-8')
            if output.strip() != 'check':
                err = output
        except OSError as exc:
            err = str(exc)
        except subprocess.CalledProcessError as exc:
            err = exc.output.decode('utf-8')
        if err is not None:
            self._available = False
            raise ShellError('{} check error: {}'.format(self, err))
        else:
            self._available = True

    def is_available(self):
        try:
            return self._available
        except AttributeError:
            raise ShellError('call check() first')

    def __call__(self, *args):
        return self._command + args

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{}>'.format(self.name)


Shell.BASH = Shell('Bash', 'bash -c')
Shell.ZSH = Shell('Zsh', 'zsh -c')
# TODO: add support for POSIX shells
# Shell.ASH = Shell('ash', 'ash -c')
# Shell.DASH = Shell('Dash', 'dash -c')
# Shell.BASH_POSIX = Shell('Bash POSIX', 'bash --posix -c')


SHELLS = dict(inspect.getmembers(Shell, lambda o: isinstance(o, Shell)))


class ScriptRunner(object):

    _proc = None
    _output = None

    def __init__(self, shell, shellsrc_path, luamb_dir):
        self._shell = shell
        self._shellsrc_path = shellsrc_path
        self._env = {
            'LUAMB_DIR': luamb_dir,
        }

    def __call__(self, script):
        script = """
            . {shellsrc_path}
            {script}
        """.format(shellsrc_path=self._shellsrc_path, script=script)
        proc = subprocess.Popen(
            self._shell(script),
            env=self._env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        proc.wait()
        self._proc = proc
        return proc.returncode

    def __getitem__(self, key):
        return self._env[key]

    def __setitem__(self, key, value):
        self._env[key] = value

    def __delitem__(self, key):
        del self._env[key]

    @property
    def output(self):
        if self._output is not None:
            return self._output
        self._output = self._proc.stdout.read().strip().decode('utf-8')
        return self._output
