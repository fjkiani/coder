from hc.pollers import RestPoller
from rs import Cluster
from hc.formatters import BashFormatter
from prometheus_client import make_wsgi_app, Gauge, CollectorRegistry, Summary
from wsgiref.simple_server import make_server
from sl import util

import argparse
import json
import log4p

from apscheduler.schedulers.background import BackgroundScheduler

logger = log4p.GetLogger('SL', config='log4p.json')
log = logger.logger

def load_args():
    parser = argparse.ArgumentParser(description='Sets slowlog config or publishes slowlog telemetry')
    parser.add_argument("action", help="the action to perform", choices=['telemetry','config'])
    parser.add_argument("fqdn_host", help="cluster endpoint host url.  Should not include scheme or port")
    parser.add_argument("cluster_username", help="cluster username")
    parser.add_argument("cluster_password", help="cluster password")
    parser.add_argument("--db", help="The database name or id to run action against.  Can be specified more than once", action='append')
    parser.add_argument("--slower-than", help="set slowlog-log-slower-than config", type=int)
    parser.add_argument("--max-len", help="set slowlog-max-len config", type=int)
    parser.add_argument("--server", help="run in server mode.  only applies when action is 'telemetry'", action='store_const', const='server', default=False)
    parser.add_argument("--server-port", help="Port to run server on.  Defaults to 8000", default=8000, type=int)
    parser.add_argument("--interval", help="How often to poll slowlogs when running in server mode (seconds).  Defaults to 5", default=5, type=int)
    parser.add_argument('--noverify', action='store_const', const="noverify", default=False,
                    help='whether or not to verify server certificate)')

    return parser.parse_args()

def use_db(args, db):
    if (args.db is None):
        return True
    return str(db.descriptor["uid"]) in args.db or db.descriptor["name"] in args.db

def set_config(args):
    c = Cluster.Cluster(fqdn_host=args.fqdn_host, cluster_username=args.cluster_username, cluster_password=args.cluster_password, verify=not args.noverify)
    dbs = c.databases()
    for db in dbs:
        if (use_db(args, db)):
            if (args.slower_than):
                db.slowlogslowerthan_set(args.slower_than)
            if (args.max_len):
                db.slowlogsmaxlen_set(args.max_len)

def get_config(args):
    c = Cluster.Cluster(fqdn_host=args.fqdn_host, cluster_username=args.cluster_username, cluster_password=args.cluster_password, verify=not args.noverify)
    dbs = c.databases()
    for db in dbs:
        if (use_db(args, db)):
            print(BashFormatter.Color.green("Name: %s Slower than: %s Max length: %s" % (db.descriptor['name'], *db.slowlogconfig_get())))

def get_slowlog(args, gauge=None):
    sls = util.get_slowlog(args.fqdn_host, args.cluster_username, args.cluster_password, verify=not args.noverify, filter_dbs=args.db)
    for sl in sls:
        if sl["metric"]["name"] == "slowlog_count":
            if gauge is not None:
                gauge.labels(sl["source"]["cluster"], sl["source"]["db"]).set(sl["metric"]["value"])
            print(BashFormatter.Color.red(json.dumps(sl)))
        else:
            log.error("%s %s %s %s" % (sl['source']['cluster'], sl['source']['db'], sl['source']['slowlog_id'], sl['metric']['value']))

def validate(args):
    pass

if __name__ == "__main__":
    args = load_args()

    validate(args)

    if (args.action == 'config'):
        if (args.slower_than is None and args.max_len is None):
            get_config(args)
        else:
            set_config(args)
    else:
        if (args.server):
            sched = BackgroundScheduler()

            sched.start()

            M_REGISTRY = CollectorRegistry()
            g = Gauge('slowlog_count', 'Number of slowlog entries in database', ['cluster','bdb_name'], registry=M_REGISTRY)

            POLL_TIME = Summary("slowlog_poll_with_timing", "Time spent polling slowlog", registry=M_REGISTRY)
            @sched.scheduled_job('interval', seconds = args.interval)
            @POLL_TIME.time()
            def poll():
                get_slowlog(args, g)

            def my_app(environ, start_fn):
                if environ['PATH_INFO'] == '/metrics':
                    return metrics_app(environ, start_fn)
                start_fn('200 OK', [])
                return [b'Please use /metrics']

            metrics_app = make_wsgi_app(registry=M_REGISTRY)
            httpd = make_server('', args.server_port, my_app)
            httpd.serve_forever()
        else:
            get_slowlog(args)
