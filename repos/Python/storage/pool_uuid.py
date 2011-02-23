#!/usr/bin/env python
"""testing "virsh pool-uuid" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Web Jan 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['pool_uuid', 'check_pool_uuid', 
           'check_pool_exists']
           

import os
import sys
import re
import time
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
from lib.Python import storageAPI
from utils.Python import utils
from exception import LibvirtAPI

VIRSH_POOLUUID = "virsh pool-uuid"

def check_storage_exists(stgobj, poolname, logger):
    """ check if the pool exists, may or may not be active """
    pool_names = stgobj.storage_pool_list()
    pool_names += stgobj.defstorage_pool_list()

    if poolname not in pool_names:
        logger.error("%s doesn't exist" % poolname)
        return False
    else:
        return True

def check_pool_uuid(poolname, UUIDString, logger):
    """ check UUID String of a pool """
    status, ret = commands.getstatusoutput(VIRSH_POOLUUID + ' %s' % poolname)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_POOLUUID + ' %s' % poolname + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        UUIDString_virsh = ret[:-1]
        logger.debug("UUIDString from API is %s" % UUIDString)
        logger.debug("UUIDString from " + "\"" + VIRSH_POOLUUID + "\"" " is %s" % UUIDString_virsh)
        if UUIDString_virsh == UUIDString:
            return True
        else:
            return False
    

def pool_uuid(params):
    """ call appropriate API to generate the UUIDStirng
        of a pool , then compared to the output of command
        virsh pool-uuid
    """
    logger = params['logger']
    if 'poolname' not in params:
        logger.error("the option poolname is required") 
        return 1
    else:
        poolname = params['poolname']
           
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    stgobj = storageAPI.StorageAPI(virconn)

    if not check_storage_exists(stgobj, poolname, logger):
        logger.error("need a defined pool, may or may not be active")
        return 1

    try:
        UUIDString = stgobj.get_pool_uuidstring(poolname)
        logger.info("the UUID string of pool %s is %s" % (poolname, UUIDString))
        if check_pool_uuid(poolname, UUIDString, logger):
            logger.info(VIRSH_POOLUUID + " test succeeded.")
            return 0
        else:
            logger.error(VIRSH_POOLUUID + " test failed.")
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
(e.response()['message'], e.response()['code']))
        return 1
          
        
 
