#!/usr/bin/env python
"""testing "virsh net-uuid" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Web Jan 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['netuuid', 'check_network_uuid', 
           'check_network_exists']
           

import os
import sys
import re
import commands

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib.Python import connectAPI
from lib.Python import networkAPI
from utils.Python import utils
from exception import LibvirtAPI

VIRSH_NETUUID = "virsh net-uuid"

def check_network_exists(netobj, networkname, logger):
    """ check if the network exists, may or may not be active """
    network_names = netobj.network_list()
    network_names += netobj.defined_list()

    if networkname not in network_names:
        logger.error("%s doesn't exist" % networkname)
        return False
    else:
        return True

def check_network_uuid(networkname, UUIDString, logger):
    """ check UUID String of a network """
    status, ret = commands.getstatusoutput(VIRSH_NETUUID + ' %s' % networkname)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_NETUUID + ' %s' % networkname + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        UUIDString_virsh = ret[:-1]
        logger.debug("UUIDString from API is %s" % UUIDString)
        logger.debug("UUIDString from " + "\"" + VIRSH_NETUUID + "\"" " is %s" % UUIDString_virsh)
        if UUIDString_virsh == UUIDString:
            return True
        else:
            return False
    

def netuuid(params):
    """ call appropriate API to generate the UUIDStirng
        of a network , then compared to the output of command
        virsh net-uuid
    """
    logger = params['logger']
    if 'networkname' not in params:
        logger.error("the option networkname is required") 
        return 1
    else:
        networkname = params['networkname']
           
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    netobj = networkAPI.NetworkAPI(virconn)

    if not check_network_exists(netobj, networkname, logger):
        logger.error("need a defined network, may or may not be active")
        return 1

    try:
        UUIDString = netobj.get_uuid_string(networkname)
        logger.info("the UUID string of network %s is %s" % (networkname, UUIDString))
        if check_network_uuid(networkname, UUIDString, logger):
            logger.info(VIRSH_NETUUID + " test succeeded.")
            return 0
        else:
            logger.error(VIRSH_NETUUID + " test failed.")
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
(e.response()['message'], e.response()['code']))
        return 1
          
        
 
