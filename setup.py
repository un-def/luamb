import os
import re

from setuptools import setup


os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


with open('README.rst') as f:
    long_description = f.read()

with open('luamb.py') as f:
    author, author_email, version = re.search(
        "__author__ = '(.+) <(.+)>'.+__version__ = '([.0-9]+)'",
        f.read(),
        flags=re.DOTALL
    ).groups()


setup(
    name='luamb',
    version=version,
    py_modules=['luamb'],
    scripts=['luamb.sh'],
    install_requires=['hererocks'],
    license='MIT',
    description='Lua environment manager',
    long_description=long_description,
    url='https://github.com/un-def/luamb',
    author=author,
    author_email=author_email,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
