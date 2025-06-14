#!/usr/bin/python
# Copyright (c) 2017-2019 Forcepoint


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

   
DOCUMENTATION = '''
---
module: network_element_facts
short_description: Facts about networks elements in the SMC
description:
  - Network elements can be used as references in many areas of the
    configuration. This fact module provides the ability to retrieve
    information related to elements and their values.

version_added: '2.5'

options:
  element:
    description:
      - Type of network element to retrieve
    required: false
    default: '*'
    choices:
      - host
      - network
      - router
      - address_range
      - interface_zone
      - domain_name
      - group
      - ip_list
      - country
      - alias
      - expression
    type: str
  expand:
    description:
      - Optionally expand element attributes that contain only href
    type: list
    choices:
      - group
  
extends_documentation_fragment:
  - management_center
  - management_center_facts

requirements:
  - smc-python
author:
  - Forcepoint
'''


EXAMPLES = '''
- name: All network elements, limit result to 10
  network_element_facts:
    limit: 10

- name: Find all hosts with an IP value of 1.1.1.1 
  network_element_facts:
    limit: 0
    element: host
    filter: 1.1.1.1

- name: Find an address range including 1.1.1.1
  network_element_facts:
    limit: 10
    element: address_range
    filter: 1.1.1.1
    
- name: Find a specific group and expand all members
  network_element_facts:
    element: group
    filter: mygroup
    expand:
      - group
'''


RETURN = '''
elements:
    description: All elements, no filter
    returned: always
    type: list
    sample: [{
        "name": "Any network", 
        "type": "network"
        }, 
        {
        "name": "akamaiedge.com", 
        "type": "domain_name"
    }]

elements:
    description: Return from all elements using filter of '10.'
    returned: always
    type: list    
    sample: [{
        "comment": null, 
        "ipv4_network": "0.0.0.0/0", 
        "ipv6_network": "::/0", 
        "name": "Any network", 
        "type": "network"
        }, 
        {
        "name": "myfirewall", 
        "type": "single_fw"
        }, 
        {
        "comment": null, 
        "ipv4_network": "10.0.0.0/8", 
        "ipv6_network": null, 
        "name": "private-10.0.0.0/8", 
        "type": "network"
        }, 
        {
        "comment": null, 
        "ipv4_network": "10.10.10.0/24", 
        "ipv6_network": null, 
        "name": "network-10.10.10.0/24", 
        "type": "network"
    }]
'''

from ansible_collections.cd60.fp_ngfw_smc.plugins.module_utils.smc_util import (
    ForcepointModuleBase,
    element_type_dict,
    ro_element_type_dict,
    element_dict_from_obj)


ELEMENT_TYPES = element_type_dict()
ELEMENT_TYPES.update(ro_element_type_dict())

    
class NetworkElementFacts(ForcepointModuleBase):
    def __init__(self):
        
        self.module_args = dict(
            element=dict(type='str', choices=list(ELEMENT_TYPES.keys())),
            expand=dict(type='list', default=[])
        )
        self.element = None
        self.limit = None
        self.filter = None
        self.expand = None
        self.exact_match = None
        self.case_sensitive = None
        
        self.results = dict(
            ansible_facts=dict(
                elements=[]
            )
        )
        super(NetworkElementFacts, self).__init__(self.module_args, is_fact=True)

    def exec_module(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        
        for attr in self.expand:
            if attr not in ('group',):
                self.fail(msg='Invalid expandable attribute: %s provided. Valid '
                    'options are: group'  % attr)
        
        # Search by specific element type
        if self.element:
            result = self.search_by_type(ELEMENT_TYPES.get(self.element)['type'])
        else:
            self.element = 'network_elements'
            result = self.search_by_context()
        
        if self.filter:
            elements = [element_dict_from_obj(element, ELEMENT_TYPES, self.expand) for element in result]
        else:
            elements = [{'name': element.name, 'type': element.typeof} for element in result]
        
        self.results['ansible_facts']['elements'] = elements
        return self.results

def main():
    NetworkElementFacts()
    
if __name__ == '__main__':
    main()
