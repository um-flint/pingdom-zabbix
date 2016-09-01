#!/usr/bin/env python

import json
import re
import requests
import subprocess
import ConfigParser


config = ConfigParser.ConfigParser()
config.read('pingdom-zabbix.ini')


pingdom = dict(
    apiurl   = config.get('PINGDOM', 'apiurl'),
    appkey   = config.get('PINGDOM', 'appkey'),
    username = config.get('PINGDOM', 'username'),
    password = config.get('PINGDOM', 'password')
)


def trapper(cmd_args):
    try:
        print ' '.join(cmd_args)
        print subprocess.check_output(cmd_args)
    except subprocess.CalledProcessError as e:
        print "EXCEPTION"
        print "returncode:", e.returncode
        print "cmd:", e.cmd
        print "output:", e.output


try:
    r = requests.get(pingdom['apiurl'], auth=(pingdom['username'],pingdom['password']), headers={'App-Key': pingdom['appkey']})

    if r.status_code == requests.codes.ok:

        #
        # discovery
        #
        data = []
        for check in r.json()['checks']:
            data.append({
                'name': check['name'],
                'status': check['status'],
                'resptime': check['lastresponsetime']
            })
        discovery = []
        for check in data:
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
        trapper(cmd_args)

        #
        # status
        #
        for check in data:
            # turn 'up' into 1 and 'down' into 0
            status = 0
            if check['status'] == 'up':
                status = 1
            cmd_args = [
                'zabbix_sender',
                '-z', config.get('ZABBIX', 'server'),
                '-p', config.get('ZABBIX', 'port'),
                '-s', config.get('ZABBIX', 'host'),
                '-k', config.get('ZABBIX', 'key2') + '[' + str(check['name']) + ']',
                '-o', str(status)
            ]
            trapper(cmd_args)

        #
        # response time
        #
        for check in data:
            cmd_args = [
                'zabbix_sender',
                '-z', config.get('ZABBIX', 'server'),
                '-p', config.get('ZABBIX', 'port'),
                '-s', config.get('ZABBIX', 'host'),
                '-k', config.get('ZABBIX', 'key3') + '[' + str(check['name']) + ']',
                '-o', str(check['resptime'])
            ]
            trapper(cmd_args)

    else:
        print "EXCEPTION: Bad Request; HTTP {}".format(r.status_code)

except Exception as e:
    print "EXCEPTION: {}".format(str(e))
