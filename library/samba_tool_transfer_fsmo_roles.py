#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import ipaddress
import sys

DOCUMENTATION = r'''
'''

EXAMPLES = r'''
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
import traceback
import socket
import json
import pprint

try:
    import dns.resolver
except ImportError:
    IMPORT_ERROR = traceback.format_exc()
else:
    IMPORT_ERROR = None


def run_module():
    module_args = dict(
        away_from_adcs=dict(type='list', required=False, default=[]),
        transfer=dict(type='bool', required=False, default=False),
        domain=dict(type='str', required=True),
        administrator_password=dict(type='str', required=False),
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
        away_from_adcs = module.params['away_from_adcs']
        transfer = module.params['transfer']
        domain = module.params['domain']
        administrator_password = module.params['administrator_password']
        if not away_from_adcs and not transfer:
            module.fail_json(msg="Either away_from_adcs or transfer must be provided", **result)
        if transfer and not administrator_password:
            module.fail_json(msg="administrator_password must be provided when transfer is True", **result)

        target = find_target_adc(away_from_adcs, domain, module, result, transfer)

        rc, fsmoroles_data, out_stderr = module.run_command(["samba-tool", "fsmo", "show"], check_rc=True,
                                                            encoding="utf-8")
        result['fsmoroles'] = fsmoroles_data
        # lines look like this:
        # "SchemaMasterRole owner: CN=NTDS Settings,CN=B231969D3062,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=ad,DC=zam,DC=haus"
        fsmoroles = dict()
        for line in fsmoroles_data.splitlines():
            if "owner:" in line:
                role, owner = line.split(" owner: ")
                # role = role.replace("Role", "").strip()
                owner = owner.replace("CN=NTDS Settings,CN=", "").split(",")[0].strip()
                fsmoroles[role] = owner
        domain_ip = get_domain_ip(domain)
        fsmoroles = {
            role: (owner, get_ips(owner + "." + domain, "A", domain_ip))
            for role, owner in fsmoroles.items()
        }
        fsmoroles_changes = {
            role: (ips[0], target)
            for role, (owner, ips) in fsmoroles.items()
            if target not in ips and ips
        }
        result['fsmoroles'] = fsmoroles
        result['fsmoroles_changes'] = fsmoroles_changes
        result['changed'] = bool(fsmoroles_changes)

        role_dict = {
            "RidAllocationMasterRole": "rid",
            "SchemaMasterRole": "schema",
            "PdcEmulationMasterRole": "pdc",
            "DomainNamingMasterRole": "naming",
            "InfrastructureMasterRole": "infrastructure",
            "DomainDnsZonesMasterRole": "domaindns",
            "ForestDnsZonesMasterRole": "forestdns"
        }

        if set(fsmoroles.keys()) != set(role_dict.keys()):
            module.fail_json(
                msg=(
                        "Unexpected/Missing FSMO roles: "
                        + ", ".join(fsmoroles.keys())
                        + ";\nExpected: "
                        + ", ".join(role_dict.keys())
                ),
                **result)
        if module.check_mode:
            module.exit_json(**result)

        if not transfer:
            module.exit_json(**result)

        for role in fsmoroles_changes:
            module.run_command(
                ["samba-tool", "fsmo", "transfer", "--role", role_dict[role], "-U", "AD\\Administrator", "--password",
                 administrator_password], check_rc=True, encoding="utf-8")
    except Exception:
        # result["locals"] = pprint.pformat(locals(), indent=4)
        module.fail_json(msg=traceback.format_exc(), **result)
    else:
        # result["locals"] = pprint.pformat(locals(), indent=4)
        pass

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
