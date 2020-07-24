import os

import pytest

from luamb._shell import shellsrc

from .lib import SHELLS, ScriptRunner, ShellError


def pytest_configure():
    for key, shell in SHELLS.items():
        command = os.environ.get('TEST_SHELL_' + key)
        if command:
            shell.configure(command)
        try:
            shell.check()
        except ShellError as exc:
            exc.warn()


def pytest_generate_tests(metafunc):
    if 'script_runner' not in metafunc.fixturenames:
        return
    shell_marker = metafunc.definition.get_closest_marker('shell')
    if shell_marker is None:
        shells = SHELLS.values()
    else:
        if shell_marker.args:
            shells = shell_marker.args
            assert 'exclude' not in shell_marker.kwargs, (
                'exclude is not allowed when shell list is specified')
        else:
            exclude = shell_marker.kwargs.get('exclude')
            assert exclude, 'either shell list or exclude must be specified'
            shells = (s for s in SHELLS.values() if s not in exclude)
    params = []
    for shell in shells:
        if shell.is_available():
            param = shell
        else:
            skip_mark = pytest.mark.skip('{} is not available'.format(shell))
            param = pytest.param(shell, marks=skip_mark)
        params.append(param)
    metafunc.parametrize(
        'script_runner', params, indirect=True, ids=lambda s: repr(s))


@pytest.fixture(scope='session')
def shellsrc_path(tmp_path_factory):
    path = tmp_path_factory.mktemp('shell') / 'shellsrc'
    with open(str(path), 'w') as fo:
        fo.write(shellsrc)
    return str(path)


@pytest.fixture()
def luamb_dir(tmp_path):
    return str(tmp_path / 'luambenvs')


@pytest.fixture()
def script_runner(request, shellsrc_path, luamb_dir):
    return ScriptRunner(
        shell=request.param,
        shellsrc_path=shellsrc_path,
        luamb_dir=luamb_dir,
    )
