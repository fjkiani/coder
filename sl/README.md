# Redis Enterprise Slowlog Tool

A tool to get/set Slowlog configuration and publish Slowlog telemetry data from Redis Enterprise nodes.

## Prerequisites

- python3 
- python3-pip
- *virtualenv (Optional)*

## Installation

The archive file already contain all necessary dependencies.  To install:
- Untar the archive: tar xvf *archive*
- Change to directory: cd sl
- Create and activate a [virtualenv](https://docs.python.org/3/library/venv.html) environment, if you deem such necessary
- Install dependencies: python3 -m pip install --no-index --find-links deps/ requests re-tools

## Usage

python3 slowlog.py 
- [-h] 
- *action fqdn_host cluster_username cluster_password*
- [--db DB] 
- [--slower-than SLOWER_THAN]
- [--max-len MAX_LEN] 
- [--server]
- [--server-port SERVER_PORT]
- [--interval INTERVAL]
- [--noverify]


## Parameters
- *action* {telemetry,config}: The action to perform.  **config** to get/set Slowlog configuration, **telemetry** to get Slowlog
- *fqdn_host*: The cluster endpoint host url.  Should not include scheme or port
- *cluster_username*: A username on the cluster
- *cluster_password*: Password
- --db: The db uid or name to perform *action* on.  Can be specified more than once.  Defaults to all databases
- --noverify: Whether to skip server certificate verification.  Not to be used in production
- --server: Whether to run in server mode.  This mode will publish OpenMetrics to specified server port
- --server-port: Port to run server on.  Defaults to 8000
- --interval: How often to poll slowlogs when running in server mode (seconds).  Defaults to 5

## Examples:
### Configuration
> Get Slowlog config for all databases at host url re-n1 with supplied credentials
- python3 slowlog.py config re-n1 admin@rl.org admin
> Get Slowlog config for all databases at host url re-n1 with supplied credentials and db with uid = 1
- python3 slowlog.py config re-n1 admin@rl.org admin --db 1
> Get Slowlog config for all databases at host url re-n1 with supplied credentials and db with uid = 1 or uid = 2
- python3 slowlog.py config re-n1 admin@rl.org admin --db 1 --db 2
> Get Slowlog config for all databases at host url re-n1 with supplied credentials and db with name = my-db or uid = 2
- python3 slowlog.py config re-n1 admin@rl.org admin --db my-db --db 2
> Set Slowlog config for all databases at host url re-n1 with supplied credentials.  slowlog-log-slower-than will be 15 ms and slowlog-max-len will be 200
- python3 slowlog.py config re-n1 admin@rl.org admin --max-len 200 --slower-than 15000 
> Set Slowlog config for max length for all databases at host url re-n1 with supplied credentials.  slowlog-max-len will be 250
- python3 slowlog.py config re-n1 admin@rl.org admin --max-len 250
> Set Slowlog config for max length for only database with uid 1 at host url re-n1 with supplied credentials.  slowlog-max-len will be 350
- python3 slowlog.py config re-n1 admin@rl.org admin --max-len 350 --db 1

### Telemetry
- Get Slowlog for all databases at host re-n1 with supplied credentials
- python3 slowlog.py telemetry re-n1 admin@rl.org admin
- Get Slowlog for database with uid 1 or database with name test-db2 at host re-n1 with supplied credentials
- python3 slowlog.py telemetry re-n1 admin@rl.org admin --db 1 --db test-db2
- Get Slowlog for database with uid 1 at host re-n1 with supplied credentials
- python3 slowlog.py telemetry re-n1 admin@rl.org admin --db 1

## Logging

This tool uses [log4p](https://pypi.org/project/log4p/).  The configuration is at log4p.json

## Outstanding Items

0.2 (6/18)
- ~~Log file for elk to scrape~~
- Report prometheus OpenMetrics on all slowlog


0.1
- ~~Documentation~~
- ~~Threshold configurable on db level~~
- ~~Retrieve slowlogs~~
