# (🌑) luamb

Lua environment manager built on top of [hererocks](https://github.com/luarocks/hererocks) and inspired by [virtualenvwrapper](https://bitbucket.org/virtualenvwrapper/virtualenvwrapper).


## Supported shells

  * Bash
  * Zsh


## Installation

  1. Install `luamb` using `pip` (`hererocks` will be installed automatically):

      ```sh
      pip install [--user] luamb
      ```

  2. Create a directory for environments:

      ```sh
      mkdir $HOME/.luambenvs
      ```

  3. Configure your shell (add these lines to `~/.bashrc` or `~/.zshrc`):

      ```sh
      # path to the directory with environments
      export LUAMB_DIR=$HOME/.luambenvs

      # optional variables:
      export LUAMB_LUA_DEFAULT='lua 5.3'     # default Lua version
      export LUAMB_LUAROCKS_DEFAULT=latest   # default LuaRocks version
      LUAMB_DISABLE_COMPLETION=true          # disable shell completions
      LUAMB_PYTHON_BIN=/usr/bin/python3      # explicitly set Python executable

      # make some magic
      source <(luamb shellsrc)
      # or if luamb executable is not in PATH:
      source <("$LUAMB_PYTHON_BIN" -m luamb shellsrc)
      ```

  4. Try to execute in a new shell:

      ```sh
      luamb --help
      ```


## Examples

  * Create an environment 'myproject' with the latest Lua 5.2 (5.2.4), the latest LuaRocks and associate it with /home/user/projects/myproject:

    ```sh
    luamb mk myproject -l 5.2 -r latest -a /home/user/projects/myproject
    ```

  * Create an environment 'jittest' with LuaJIT 2.0.4, without LuaRocks and associate it with /home/user/projects/jitproj:

    ```sh
    luamb mk jittest -j 2.0.4 -a /home/user/projects/jitproj
    ```

  * Set the latest LuaJIT 2.0 (2.0.5) and the latest LuaRocks version by default:

    ```sh
    export LUAMB_LUA_DEFAULT='luajit 2.0'
    export LUAMB_LUAROCKS_DEFAULT=latest
    ```

  * Create an environment 'newenv' with the default versions and without associated project directory:

    ```sh
    luamb mk newenv
    ```

  * Create an environment 'norocks' with the default Lua version (LuaJIT 2.0.5) and without LuaRocks (verbose mode):

    ```sh
    luamb mk norocks --no-luarocks --verbose
    ```

  * Activate the 'newenv' environment:

    ```sh
    $ luamb on newenv
    ```

  * Deactivate the current environment:

    ```sh
    luamb off
    ```

  * Delete the 'myproject' environment (it will remove the environment directory only, not the project one):

    ```sh
    luamb rm myproject
    ```


## Commands

Each command has one or more aliases.

  * `on` | `enable` | `activate` — activate an environment
  * `off` | `disable` | `deactivate` — deactivate the current environment
  * `mk` | `new` | `create` — create a new environment
  * `rm` | `remove` | `del` | `delete` — remove an environment
  * `info` | `show` — Show the details for a single virtualenv
  * `ls` | `list` — list all of the environments


## Version history

  * 0.3.0 (2018-07-24)
    - Add git URIs and local paths support
    - Add hererocks non-zero status handling
    - Wrap hererocks deactivate-lua function to deactivate environment properly
    - Add some new aliases
  * 0.2.1 (2018-03-25)
    - Bugfix release
  * 0.2.0 (2017-08-29)
    - Zsh support
  * 0.1.2 (2016-08-24)
    - OS X support (using `greadlink`)
  * 0.1.1 (2016-07-23)
    - Bash completion
  * 0.1.0 (2016-07-20)
    - Initial release


## License

The [MIT License](https://github.com/un-def/luamb/blob/master/LICENSE).
