#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r'''
'''

EXAMPLES = r'''
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
import traceback
import subprocess
import json
import pprint
import os
import sys
from datetime import datetime

try:
    pass
except ImportError:
    IMPORT_ERROR = traceback.format_exc()
else:
    IMPORT_ERROR = None


def run_module():
    module_args = dict(
        since=dict(type='str', required=False),
    )
    result = dict(
        changed=False,
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    if IMPORT_ERROR is not None:
        module.fail_json(msg=IMPORT_ERROR, **result)

    try:
        since = module.params['since']
        if since is not None:
            since = datetime.strptime(since, '%Y-%m-%dT%H:%M:%S.%fZ')

        process = subprocess.run(
            ["samba-tool", "drs", "showrepl", "--json"],
            check=True,
            encoding='utf-8',
            capture_output=True,
        )
        data = json.loads(process.stdout)

        repsfrom = data['repsFrom']
        repsto = data['repsTo']
        for item in repsfrom:
            if item["last attempt message"] != "was successful":
                raise Exception(f"Last attempt was not successful: {item}")
            if item["last attempt time"] != item["last success"]:
                raise Exception(f"Last attempt was not successful: {item}")
            if since and datetime.strptime(item["last success"], "%a %b %d %H:%M:%S %Y %Z") < since:
                raise Exception(f"Last attempt was too long ago: {item}")
        for item in repsto:
            if item["last attempt message"] != "was successful":
                raise Exception(f"Last attempt was not successful: {item}")

        result["result"] = data

        if module.check_mode:
            module.exit_json(**result)

    except Exception:
        # result["locals"] = pprint.pformat(locals(), indent=4)
        module.fail_json(msg=traceback.format_exc(), **result)
    else:
        # result["locals"] = pprint.pformat(locals(), indent=4)
        pass

    # No change ops for this module, just a test
    # result['changed'] = False
    module.exit_json(**result)


def get_ips(domain, record_type, resolver_ip=None):
    resolver = dns.resolver.Resolver()
    if resolver_ip is not None:
        resolver.nameservers = [resolver_ip]
    answers = resolver.resolve(domain, record_type)
    return [answer.to_text() for answer in answers]

def to_ips(hostname_or_ip):
    try:
        ip = ipaddress.ip_address(hostname_or_ip)
        return [str(ip)]
    except ValueError:
        return get_ips(hostname_or_ip, "A")

def find_target_adc(away_from_adcs, domain,
                    module: AnsibleModule,
                    result: dict,
                    transfer):
    domain_ip = get_domain_ip(domain)
    result["domain_ip"] = domain_ip
    blacklist = {
        ip
        for adc in away_from_adcs
        for ip in to_ips(adc)
    }
    result['blacklist'] = blacklist
    whitelist = set(get_ips(domain, "A", domain_ip))
    whitelist = whitelist - blacklist
    result['whitelist'] = whitelist
    if not whitelist:
        module.fail_json(error="No valid target ADC found", **result)
    target = whitelist.pop() if not transfer else None
    result['target'] = target
    return target


def get_domain_ip(domain):
    domain_ip = get_ips(domain, "A")[0]
    return domain_ip


def main():
    run_module()


if __name__ == '__main__':
    main()
