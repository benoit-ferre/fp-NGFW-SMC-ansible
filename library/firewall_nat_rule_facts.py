#!/usr/bin/python
#
# Copyright (c) 2017-2019 Forcepoint


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: firewall_nat_rule_facts
short_description: Facts about firewall rules based on specified policy
description:
  - Retrieve rule specific information based on the policy specified in the
    facts module run. Specifying the policy is a required field. In addition,
    you can choose to expand fields like source, destination and services from
    href to their native element type and name by using the expand list with
    specified fields to expand. There are other search capabilities such as
    finding a rule based on partial match and rules within specific ranges.

version_added: '2.5'

options:
  filter:
    description:
      - The name of the firewall Policy for which to retrieve rules
    required: true
  search:
    description:
      - Provide a search string for which to use as a match against a rule/s
        name or comments field. Mutually exclusive with I(rule_range)
    type: str
  rule_range:
    description:
      - Provide a rule range to retrieve. Firewall rules will be displayed based
        on the ranges provided in a top down fashion.
    type: str
  expand:
    description:
      - Specifying fields which should be expanded from href into their
        native elements. Expanded fields will be returned as a dict of lists
        with the key being the element type and list being the name values for
        that element type
    choices:
      - source
      - destination
      - services
    type: list
  as_yaml:
    description:
      - Set this boolean to true if the output should be exported into yaml format. By
        default the output format is actually dict, but using this field allows you to
        also use the provided jinja templates to format into yaml and reuse for playbook
        runs.
    type: bool
  
extends_documentation_fragment:
  - management_center
  - management_center_facts

requirements:
  - smc-python >= 0.6.0
author:
  - Forcepoint
'''

EXAMPLES = '''
- name: Facts about all engines within SMC
  hosts: localhost
  gather_facts: no
  tasks:
  - name: Show rules for policy 'TestPolicy' (only shows name, type)
    firewall_nat_rule_facts:
      filter: TestPolicy

  - name: Search for specific rule/s using search value (partial searching supported)
    firewall_nat_rule_facts:
      filter: TestPolicy
      search: rulet

  - name: Dump the results in yaml format, showing details of rule
    firewall_nat_rule_facts:
      filter: TestPolicy
      search: rulet
      as_yaml: true

  - name: Resolve the source, destination and services fields
    firewall_nat_rule_facts:
      filter: TestPolicy
      search: rulet
      as_yaml: true
      expand:
      - sources
      - destinations
      - services

  - name: Get specific rules based on range order (rules 1-10)
    firewall_nat_rule_facts:
      filter: TestPolicy
      rule_range: 1-3
      as_yaml: true
  
  - name: Get firewall rule as yaml
    firewall_nat_rule_facts:
      smc_logging:
       level: 10
       path: ansible-smc.log
      filter: TestPolicy
      search: rulet
      #rule_range: 1-3
      as_yaml: true
      expand:
      - services
      - destinations
      - sources
  
  - name: Write the yaml using a jinja template
    template: src=templates/facts_yaml.j2 dest=./firewall_nat_rules_test.yml
    vars:
      playbook: firewall_rule
'''


RETURN = '''
firewall_nat_rule: 
    description: Obtain metadata through a simple rule search
    returned: always
    type: list
    sample: [
    {
        "policy": "TestPolicy", 
        "rules": [
            {
                "name": "Rule @125.4", 
                "pos": 1, 
                "type": "fw_ipv4_nat_rule"
            }, 
            {
                "name": "Rule @122.5", 
                "pos": 2, 
                "type": "fw_ipv4_nat_rule"
            }, 
            {
                "name": "Rule @121.4", 
                "pos": 3, 
                "type": "fw_ipv4_nat_rule"
            }]
    }]

'''

import traceback
from ansible_collections.cd60.fp_ngfw_smc.plugins.module_utils.smc_util import ForcepointModuleBase

try:
    from smc.api.exceptions import SMCException
    from smc.policy.layer3 import FirewallPolicy
except ImportError:
    pass


engine_type = ('single_fw', 'single_layer2', 'single_ips', 'virtual_fw',
    'fw_cluster', 'master_engine')


def to_yaml(rule, expand=None):
    _rule = {
        'name': rule.name, 'tag': rule.tag,
        'is_disabled': rule.is_disabled,
        'comment': rule.comment}
    
    if getattr(rule, 'used_on', None) is not None:
        if getattr(rule.used_on, 'name', None):
            _rule.update(used_on=rule.used_on.name)
        else:
            _rule.update(used_on=rule.used_on)
    
    for field in ('sources', 'destinations', 'services'):
        if getattr(rule, field).is_any:
            _rule[field] = {'any': True}
        elif getattr(rule, field).is_none:
            _rule[field] = {'none': True}
        else:
            if expand and field in expand:
                tmp = {}
                for entry in getattr(rule, field).all():
                    element_type = entry.typeof
                    if entry.typeof in engine_type:
                        element_type = 'engine'
                    elif 'alias' in entry.typeof:
                        element_type = 'alias'
                    tmp.setdefault(element_type, []).append(
                        entry.name)
            else:
                tmp = getattr(rule, field).all_as_href()
            _rule[field] = tmp
    
    for nat in ('dynamic_src_nat', 'static_src_nat', 'static_dst_nat'):
        if getattr(rule, nat).has_nat:
            nat_rule = getattr(rule, nat)
            if 'static_dst_nat' in nat:
                if nat_rule.original_value.min_port:
                    original_value = nat_rule.get(nat).get('original_value')
                    original_value.pop('element', None)
                    original_value.pop('ip_descriptor', None)
                else:
                    nat_rule.get(nat).pop('original_value', None)
            else:
                nat_rule.get(nat).pop('original_value', None)
                   
            _rule[nat] = nat_rule.data.get(nat)
            
            translated_value = nat_rule.translated_value.data
            if nat_rule.translated_value.element:
                element = nat_rule.translated_value.as_element
                translated_value.pop('element', None)
                translated_value.pop('ip_descriptor', None)
                translated_value.update(
                    type=element.typeof,
                    name=element.name)
            else:
                translated_value.update(
                    ip_descriptor=nat_rule.translated_value.ip_descriptor)   
            
            _attr = 'translated_value' if not 'dynamic_src_nat' in nat \
                    else 'translation_values'
            nat_rule.get(nat).pop(_attr, None)
            nat_rule.get(nat).update(
                translated_value=translated_value)

    return _rule


expands = ('sources', 'destinations', 'services')


class FirewallNATRuleFacts(ForcepointModuleBase):
    def __init__(self):
        
        self.module_args = dict(
            filter=dict(type='str', required=True),
            expand=dict(type='list', default=[]),
            search=dict(type='str'),
            rule_range=dict(type='str')
        )
    
        self.expand = None
        self.search = None
        self.limit = None
        self.filter = None
        self.as_yaml = None
        self.exact_match = None
        self.case_sensitive = None
        
        mutually_exclusive = [
            ['search', 'rule_range'],
        ]
        
        self.results = dict(
            ansible_facts=dict(
                firewall_nat_rule=[]
            )
        )
        super(FirewallNATRuleFacts, self).__init__(self.module_args, is_fact=True,
            mutually_exclusive=mutually_exclusive)

    def exec_module(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        
        for attr in self.expand:
            if attr not in expands:
                self.fail(msg='Invalid expandable attribute: %s provided. Valid '
                    'options are: %s'  % (attr, expands))
        
        rules = []
        try:
            policy = self.search_by_type(FirewallPolicy)
            if not policy:
                self.fail(msg='Policy specified could not be found: %s' % self.filter)
            elif len(policy) > 1:
                self.fail(msg='Multiple policies found with the given search filter: %s '
                    'Use exact_match or case_sensitive to narrow the search' % 
                    [p.name for p in policy])
    
            policy = policy.pop()
            
            if self.search:
                result = policy.search_rule(self.search)
            elif self.rule_range:
                try:
                    start, end = map(int, self.rule_range.split('-'))
                    result= [x for x in policy.fw_ipv4_nat_rules][start-1:end]
                except ValueError:
                    raise SMCException('Value of rule range was invalid. Rule ranges '
                        'must be a string with numeric only values, got: %s' %
                        self.rule_range)
            else:
                result = policy.fw_ipv4_nat_rules
            
            if self.as_yaml:
                rules = [to_yaml(rule, self.expand) for rule in result
                         if rule.typeof == 'fw_ipv4_nat_rule']
            else:
                # No order for since rules could be sliced or searched
                if self.search or self.rule_range:
                    rules = [{'name': rule.name, 'type': rule.typeof} for rule in result
                             if rule.typeof == 'fw_ipv4_nat_rule']
                else:
                    rules = [{'name': rule.name, 'type': rule.typeof, 'pos': num}
                              for num, rule in enumerate(result, 1)]
        
        except SMCException as err:
            self.fail(msg=str(err), exception=traceback.format_exc())
        
        firewall_rule = {
            'policy': policy.name,
            'rules': rules}
    
        self.results['ansible_facts']['firewall_nat_rule'].append(firewall_rule)
        return self.results
        
        
def main():
    FirewallNATRuleFacts()
    
if __name__ == '__main__':
    main()
