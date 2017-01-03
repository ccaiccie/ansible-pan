#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: panos_check
short_description: check if PAN-OS device is ready for configuration
description:
    - Check if PAN-OS device is ready for being configured (no pending jobs).
    - The check could be done once or multiple times until the device is ready.
author:
    - Palo Alto Networks
    - Luigi Mori (jtschichold)
version_added: "0.0"
requirements:
    - pan-python
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
    password:
        description:
            - password for authentication
        required: true
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    timeout:
        description:
            - timeout of API calls
        required: false
        default: "0"
    interval:
        description:
            - time waited between checks
        required: false
        default: "0"
'''

EXAMPLES = '''
# single check on 192.168.1.1 with credentials admin/admin
- name: check if ready
  panos_check:
    ip_address: "192.168.1.1"
    password: "admin"

# check for 10 times, every 30 seconds, if device 192.168.1.1
# is ready, using credentials admin/admin
- name: wait for reboot
  panos_check:
    ip_address: "192.168.1.1"
    password: "admin"
  register: result
  until: not result|failed
  retries: 10
  delay: 30
'''

import sys
import time

try:
    import pan.xapi
except ImportError:
    print "failed=True msg='pan-python required for this module'"
    sys.exit(1)


def check_jobs(jobs, module):
    job_check = False
    for j in jobs:
        status = j.find('.//status')
        if status is None:
            return False
        if status.text != 'FIN':
            return False
        job_check = True
    return job_check


def main():
    argument_spec = dict(
        ip_address=dict(default=None),
        password=dict(default=None, no_log=True),
        username=dict(default='admin'),
        timeout=dict(default=0, type='int'),
        interval=dict(default=0, type='int')
    )
    module = AnsibleModule(argument_spec=argument_spec)

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")
    username = module.params['username']
    timeout = module.params['timeout']
    interval = module.params['interval']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password,
        timeout=60
    )

    checkpnt = time.time()+timeout
    while True:
        try:
            xapi.op(cmd="show jobs all", cmd_xml=True)
        except:
            pass
        else:
            jobs = xapi.element_root.findall('.//job')
            if check_jobs(jobs, module):
                module.exit_json(changed=True, msg="okey dokey")

        if time.time() > checkpnt:
            break

        time.sleep(interval)

    module.fail_json(msg="Timeout")

from ansible.module_utils.basic import *   # noqa

main()
