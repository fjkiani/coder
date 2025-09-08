import pytest
from sl import util
from rs import Cluster, Database
from .slowlog_response import slowlog

CLUSTER_HOST = "cluster_host"
CLUSTER_USER = "username"
CLUSTER_PASS = "password"


def test_get_slowlog(mocker):
    mocker.patch.object(Cluster.Cluster, 'fetch_url', return_value=(
        200, [{'name': 'db-1', 'uid': "1"}]))
    mocker.patch.object(Database.Database, 'execute_command', side_effect=[(200, {'response':100}), slowlog])

    sl = list(util.get_slowlog(CLUSTER_HOST, CLUSTER_USER, CLUSTER_PASS, verify=False))

    assert(sl[0]['metric']['name'] == 'slowlog_count')
    assert(sl[0]['metric']['value'] == 100)
    assert(len(sl) == 113)
