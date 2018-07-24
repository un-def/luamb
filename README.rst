(🌑) luamb
==========

Lua environment manager built on top of
`hererocks <https://github.com/mpeterv/hererocks>`__ and inspired by
`virtualenvwrapper <https://bitbucket.org/virtualenvwrapper/virtualenvwrapper>`__.

Supported shells
~~~~~~~~~~~~~~~~

-  Bash
-  Zsh

Installation
~~~~~~~~~~~~

1. Install ``luamb`` (``hererocks`` will be installed automatically):

   ::

       $ pip install luamb

2. Create directory for environments:

   ::

       $ mkdir $HOME/.luambenvs

3. Configure your shell (add these lines to ``~/.bashrc`` or ``~/.zshrc``):

   .. code:: shell

       # path to directory with environments
       export LUAMB_DIR=$HOME/.luambenvs

       # optional variables:
       export LUAMB_LUA_DEFAULT=lua5.3        # default Lua version
       export LUAMB_LUAROCKS_DEFAULT=latest   # default LuaRocks version
       LUAMB_COMPLETION=true                  # enable shell completion
       LUAMB_PYTHON_BIN=/usr/bin/python3      # explicitly set Python executable

       # make some magic
       source "$(which luamb.sh)"             # or absolute path like /usr/local/bin/luamb.sh

4. Try to execute in new shell:

   ::

       $ luamb --help

Examples
~~~~~~~~

-  Create environment 'myproject' with latest Lua 5.2 (5.2.4), latest
   LuaRocks and associate it with /home/user/projects/myproject:

   ::

       $ luamb mk myproject -l 5.2 -r latest -a /home/user/projects/myproject

-  Create environment 'jittest' with LuaJIT 2.0.4, without LuaRocks and
   associate it with /home/user/projects/jitproj:

   ::

       $ luamb mk jittest -j 2.0.4 -a /home/user/projects/jitproj

-  Set LuaJIT 2.0 (2.0.4) and latest LuaRocks version by default:

   ::

       $ export LUAMB_LUA_DEFAULT=luajit2.0
       $ export LUAMB_LUAROCKS_DEFAULT=latest

-  Create environment 'newenv' with default versions and without
   associated project directory:

   ::

       $ luamb mk newenv

-  Create environment 'norocks' with default Lua version (LuaJIT 2.0.4)
   and without LuaRocks (verbose mode):

   ::

       $ luamb mk norocks --no-luarocks --verbose

-  Activate 'newenv' environment:

   ::

       $ luamb on newenv

-  Deactivate current environment:

   ::

       $ luamb off

-  Delete 'myproject' environment (it will remove env dir only, not
   project dir):

   ::

       $ luamb rm myproject

Commands
~~~~~~~~

Each command has one or more alias.

``on`` \| ``enable`` \| ``activate`` — activate environment

``off`` \| ``disable`` \| ``deactivate`` — deactivate current environment

``mk`` \| ``new`` \| ``create`` — create new environment

``rm`` \| ``remove`` \| ``del`` \| ``delete`` — remove environment

``info`` \| ``show`` — show environment info

``ls`` \| ``list`` — list all environments

Version history
~~~~~~~~~~~~~~~

-  0.3.0 (2018-07-24)

   -  Add git URIs and local paths support
   -  Add hererocks non-zero status handling
   -  Wrap hererocks deactivate-lua function to deactivate environment properly
   -  Add some new aliases

-  0.2.1 (2018-03-25)

   -  Bugfix release

-  0.2.0 (2017-08-29)

   -  Zsh support

-  0.1.2 (2016-08-24)

   -  OS X support (using ``greadlink``)

-  0.1.1 (2016-07-23)

   -  Bash completion

-  0.1.0 (2016-07-20)

   -  Initial release

License
~~~~~~~

See `LICENSE <https://github.com/un-def/luamb/blob/master/LICENSE>`__.
