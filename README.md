(🌑) luamb
=========

Lua environment manager built on top of [hererocks](https://github.com/mpeterv/hererocks).



### Installation

...



### Examples

* create environment 'myproject' with latest Lua 5.2 (5.2.4), latest LuaRocks and associate it with /home/user/projects/myproject:
```
$ luamb mk myproject -l 5.2 -r latest -a /home/user/projects/myproject
```

* set LuaJIT 2.0 (2.0.4) and latest LuaRocks version by default:
```
$ export LUAMB_LUA_DEFAULT=luajit2.0
$ export LUAMB_LUAROCKS_DEFAULT=latest
```

* create environment 'newenv' with default versions and without associated project directory:
```
$ luamb mk newenv
```

* create environment 'norocks' with default Lua version (LuaJIT 2.0.4) and without LuaRocks (verbose mode):
```
$ luamb mk norocs --no-luarocks --verbose
```

* activate 'newenv' environment:
```
$ luamb on newenv
```

* deactivate current environment:
```
$ luamb off
```

* delete 'myproject' environment (it will remove env dir only, not project dir):
```
$ luamb rm myproject
```


### Commands

Each command has one or more alias.

`on` | `activate` — activate existing environment

`off` | `disable` — deactivate current environment

`mk` | `new` | `create` — create new environment

`rm` | `remove` | `del` — delete existing environment

`ls` | `list` — list all environments
