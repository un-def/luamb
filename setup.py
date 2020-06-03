import codecs
import os
import re

from setuptools import find_packages, setup

this_dir = os.path.abspath(os.path.dirname(__file__))
package_dir = os.path.join(this_dir, 'src', 'luamb')


def read(*path):
    file_path = os.path.join(*path)
    with codecs.open(file_path, encoding='utf-8') as file_obj:
        return file_obj.read()


author, author_email, version = re.search(
    r"__author__ = '(.+) <(.+)>'\n__version__ = '([.0-9a-z]+)'",
    read(package_dir, 'version.py'),
).groups()


setup(
    name='luamb',
    version=version,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=True,
    install_requires=['hererocks'],
    entry_points={
        'console_scripts': ['luamb = luamb._entrypoint:main'],
    },
    license='MIT',
    description='Lua environment manager',
    long_description=read(this_dir, 'README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/un-def/luamb',
    author=author,
    author_email=author_email,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
