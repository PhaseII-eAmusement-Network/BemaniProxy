# BemaniProxy
An expanded version of the bemaniutils proxy server

## Why?
I wanted to make a dedicated proxy app that can be production hosted, and decided to leave the standard bemaniutils proxy alone.

## About
Currently, we're just using SQLite3 as the DB.

## Setup
Requires Python 3.12 or higher. I suggest creating a virtual env for this application.

`python -m venv venv` (creates a virtual env as `venv`) (and then activate the venv)

Once in your virtual env, run `pip install --upgrade pip` and `pip install -r requirements.txt`

After pip finishes, you can run `dbadmin` and `proxy`.

## DBAdmin
this is dogshit temp ai slop that i built to easily test and make the db

will be replaced with real tools

## proxy
This is the core proxy server. It can be started purely with args or with a config file.

```fix
usage: proxy [-h] [-p PORT] [-a ADDRESS] [-r REAL_ADDRESS] -q REMOTE_PORT -b REMOTE_ADDRESS [-c CONFIG] [-k KEEPALIVE] [-v] [-t TIMEOUT]

A utility to MITM non-SSL eAmusement connections. Upgraded.

options:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port to listen on. Defaults to 9090
  -a ADDRESS, --address ADDRESS
                        Address to listen on. Defaults to all addresses
  -r REAL_ADDRESS, --real-address REAL_ADDRESS
                        Real address we are listening on (for NAT and such)
  -q REMOTE_PORT, --remote-port REMOTE_PORT
                        Port to connect to.
  -b REMOTE_ADDRESS, --remote-address REMOTE_ADDRESS
                        Address to connect to.
  -c CONFIG, --config CONFIG
                        Configuration file for PCBID to remote server mapping.
  -k KEEPALIVE, --keepalive KEEPALIVE
                        Keepalive domain to advertise. Defaults to localhost
  -v, --verbose         Display verbose packet info.
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout (in seconds) for proxy requests. Defaults to 30 seconds.
```

(currently the config file doesn't work, don't use it)

# Open Source Software
This tool largely uses code from [DragonMinded/bemaniutils](https://github.com/DragonMinded/bemaniutils) as a base.
