#!/usr/bin/env python
"""testing "virsh pool-name" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Web Jan 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['pool_name', 'check_pool_uuid',
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

VIRSH_POOLNAME = "virsh pool-name"

def check_pool_exists(stgobj, poolname, logger):
    """ check if the pool exists, may or may not be active """
    pool_names = stgobj.storage_pool_list()
    pool_names += stgobj.defstorage_pool_list()

    if poolname not in pool_names:
        logger.error("%s doesn't exist" % poolname)
        return False
    else:
        return True

def check_pool_uuid(poolname, UUIDString, logger):
    """ check the output of virsh pool-name """
    status, ret = commands.getstatusoutput(VIRSH_POOLNAME + ' %s' % UUIDString)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_POOLNAME + ' %s' % UUIDString + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        poolname_virsh = ret[:-1]
        logger.debug("poolname from " + VIRSH_POOLNAME + " is %s" % poolname_virsh)
        logger.debug("poolname we expected is %s" % poolname)
        if poolname_virsh == poolname:
            return True
        else:
            return False

def pool_name(params):
    """ get the UUIDString of a pool, then call
        virsh pool-name to generate the name of pool,
        then check it
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

    if not check_pool_exists(stgobj, poolname, logger):
        logger.error("need a defined pool, may or may not be active")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    try:
        UUIDString = stgobj.get_pool_uuidstring(poolname)
        logger.info("the UUID string of pool %s is %s" % (poolname, UUIDString))
        if check_pool_uuid(poolname, UUIDString, logger):
            logger.info(VIRSH_POOLNAME + " test succeeded.")
            return 0
        else:
            logger.error(VIRSH_POOLNAME + " test failed.")
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
