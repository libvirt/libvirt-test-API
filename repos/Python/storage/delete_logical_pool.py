#!/usr/bin/env python
"""this test case is used for testing delete
   a logical type storage pool
"""

__author__ = 'Johnny Liu: jialiu@redhat.com'
__date__ = 'Jun 13, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_delete_pool', 'delete_logical_pool', \
           'display_pool_info', 'display_physical_volume']

import os
import re
import sys
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


def usage(params):
    """Verify inputing parameter dictionary"""
    keys = ['poolname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            logger.info("please input the following argument:")
            logger.info(keys)
            return False
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return False
        else:
            return True

def display_pool_info(stgobj):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" \
                 % stgobj.defstorage_pool_list())
    logger.debug("current active storage pool: %s" \
                 % stgobj.storage_pool_list())

def display_physical_volume():
    """Display volume group and physical volume information"""
    stat1, ret1 = commands.getstatusoutput("pvdisplay")
    if stat1 == 0:
        logger.debug("pvdisplay command executes successfully")
        logger.debug(ret1)
    else:
        logger.error("fail to execute pvdisplay command")

    stat2, ret2 = commands.getstatusoutput("vgdisplay")
    if stat2 == 0:
        logger.debug("vgdisplay command executes successfully")
        logger.debug(ret2)
    else:
        logger.error("fail to execute pvdisplay command")

def check_delete_pool(poolname):
    """Check delete storage pool result,
       /etc/lvm/backup/pool_name will not exist if pool delete is successful
    """
    path = "/etc/lvm/backup/%s" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))
    if os.access(path, os.R_OK):
        logger.debug("%s is still existing")
        return False
    else:
        logger.debug("%s file don't exist" % path)
        return True


def delete_logical_pool(params):
    """delete a storage pool"""
    global logger
    logger = params['logger']

    if not usage(params):
        return 1

    poolname = params['poolname']

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(virconn)

    if check_delete_pool(poolname):
        logger.debug("%s storage pool is deleted" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    display_pool_info(stgobj)
    display_physical_volume()

    try:
        logger.info("delete %s storage pool" % poolname)
        stgobj.delete_pool(poolname)
        display_pool_info(stgobj)
        display_physical_volume()

        if check_delete_pool(poolname):
            logger.info("delete %s storage pool is successful" % poolname)
            return 0
        else:
            logger.error("fail to delete %s storage pool" % poolname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
