(🌑) luamb
=========

Lua environment manager built on top of
`hererocks <https://github.com/mpeterv/hererocks>`__ and inspired by
`virtualenvwrapper <https://bitbucket.org/virtualenvwrapper/virtualenvwrapper>`__.

Installation
~~~~~~~~~~~~

1. Install ``luamb`` (``hererocks`` will be installed automatically):

   ::

       $ pip install luamb

2. Create directory for envs:

   ::

       $ mkdir $HOME/.luambenvs

3. Configure your shell (add these lines to ``~/.bashrc``):

   ::

       export LUAMB_DIR=$HOME/.luambenvs
       source /usr/local/bin/luamb.sh          # default path in Debian if luamb has been installed globally
       # optional variables:
       # LUAMB_LUA_DEFAULT=lua5.3              # default Lua version
       # LUAMB_LUAROCKS_DEFAULT=latest         # default LuaRocks version
       # LUAMB_PYTHON_BIN=/usr/bin/python3     # explicitly set Python executable

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

``on`` \| ``enable`` — activate existing environment

``off`` \| ``disable`` — deactivate current environment

``mk`` \| ``new`` \| ``create`` — create new environment

``rm`` \| ``remove`` \| ``del`` — delete existing environment

``ls`` \| ``list`` — list all environments
