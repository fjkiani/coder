from hc.pollers import RestPoller

def get_slowlog(fqdn_host, cluster_username, cluster_password, verify=True, filter_dbs=None):
    def use_db(db):
        if (filter_dbs is None):
            return True
        return str(db.uid()) in filter_dbs or db.name() in filter_dbs  

    r = RestPoller.RestPoller(fqdn_host, cluster_username, cluster_password, verify=verify, accept_db=use_db)
    sls = r._RestPoller__poll_slowlog()
    for sl in sls:
        yield sl