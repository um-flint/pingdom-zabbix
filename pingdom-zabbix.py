#!/usr/bin/env python

#
# modules
#
import json
import re
import requests
import subprocess
import ConfigParser

#
# pull in the config
#
config = ConfigParser.ConfigParser()
config.read('pingdom-zabbix.ini')

#
# zabbix trapper call
#
def zabbix_trapper(cmd_args):
    try:
        print ' '.join(cmd_args)
        print subprocess.check_output(cmd_args)
    except subprocess.CalledProcessError as e:
        print "EXCEPTION"
        print "returncode:", e.returncode
        print "cmd:", e.cmd
        print "output:", e.output

#
# pull pingdom data (checks and values)
#
def pingdom_data(pingdom_response):
    data = []
    for check in pingdom_response.json()['checks']:
        data.append({
            'name': check['name'],
            'status': check['status'],
            'resptime': check['lastresponsetime']
        })
    return data

#
# pingdom checks -> zabbix discovery
#
def zabbix_discovery(pingdom_data):
    discovery = []
    for check in pingdom_data:
        discovery.append(
            {"{#NAME}": str(check['name'])}
        )
    cmd_args = [
        'zabbix_sender',
        '-z', config.get('ZABBIX', 'server'),
        '-p', config.get('ZABBIX', 'port'),
        '-s', config.get('ZABBIX', 'host'),
        '-k', config.get('ZABBIX', 'key1'),
        '-o', "'{ \"data\": " + json.dumps(discovery) + " }'"
    ]
    zabbix_trapper(cmd_args)

#
# pingdom status -> zabbix trapper
#
def zabbix_status(pingdom_data):
    for check in pingdom_data:
        # turn 'up' into 1 and 'down' into 0
        status = 0
        if check['status'] == 'up':
            status = 1
        cmd_args = [
            'zabbix_sender',
            '-z', config.get('ZABBIX', 'server'),
            '-p', config.get('ZABBIX', 'port'),
            '-s', config.get('ZABBIX', 'host'),
            '-k', '\'' + config.get('ZABBIX', 'key2') + '[' + str(check['name']) + ']\'',
            '-o', str(status)
        ]
        zabbix_trapper(cmd_args)

#
# pingdom lastresponsetime -> zabbix trapper
#
def zabbix_resptime(pingdom_data):
    for check in data:
        cmd_args = [
            'zabbix_sender',
            '-z', config.get('ZABBIX', 'server'),
            '-p', config.get('ZABBIX', 'port'),
            '-s', config.get('ZABBIX', 'host'),
            '-k', '\'' + config.get('ZABBIX', 'key3') + '[' + str(check['name']) + ']\'',
            '-o', str(check['resptime'])
        ]
        zabbix_trapper(cmd_args)

try:
    # pingdom variables (convenience)
    pingdom = dict(
        apiurl   = config.get('PINGDOM', 'apiurl'),
        appkey   = config.get('PINGDOM', 'appkey'),
        username = config.get('PINGDOM', 'username'),
        password = config.get('PINGDOM', 'password')
    )
    # connect to pingdom
    res = requests.get(pingdom['apiurl'], auth=(pingdom['username'],pingdom['password']), headers={'App-Key': pingdom['appkey']})
    if res.status_code == requests.codes.ok:
        # fetch pingdom data (checks and values)
        data = pingdom_data(res)
        # pingdom checks -> zabbix discovery
        zabbix_discovery(data)
        # pingdom status and lastresponsetime -> zabbix values
        zabbix_status(data)
        zabbix_resptime(data)
    else:
        print "EXCEPTION: Bad Request; HTTP {}".format(str(res.status_code))

except Exception as e:
    print "EXCEPTION: {}".format(str(e))
