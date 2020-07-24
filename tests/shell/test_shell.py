import pytest


def test_shellsrc(script_runner):
    exit_status = script_runner('')
    assert exit_status == 0
    assert script_runner.output == ''


@pytest.mark.parametrize('env_name,is_valid', [
    ('', False),
    ('.', False),
    ('..', False),
    ('foo/bar', False),
    ('/foo', False),
    ('foo/', False),
    ('/', False),
    ('...', True),
    ('foo', True),
    ('foo bar', True),
])
def test_check_env_name(script_runner, env_name, is_valid):
    exit_status = script_runner("__luamb_check_env_name '{}'".format(env_name))
    output = script_runner.output
    if is_valid:
        assert exit_status == 0
        assert output == ''
    else:
        assert exit_status != 0
        assert output == "invalid env name: '{}'".format(env_name)
