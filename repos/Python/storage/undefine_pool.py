#!/usr/bin/env python
"""this test case is used for testing undefine 
   a specific name storage pool
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu May 20, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_pool_undefine', 'check_pool_active', \
           'check_pool_inactive', 'display_pool_info', 'undefine_pool']


import os
import re
import sys

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

def display_pool_info(stg):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def check_pool_inactive(stgobj, poolname):
    """Check to make sure that the pool is defined and inactivate"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names += stgobj.storage_pool_list()
    if poolname in pool_names:
        if stgobj.isActive_pool(poolname):
            logger.error("%s pool is active" % poolname)
            return False
        else:
            return True
    else:
        logger.error("%s pool don't exist" % poolname)
        return False

def check_pool_undefine(poolname):
    """Check undefine storage pool result, if undefine storage is successful,
       poolname.xml will not exist under /etc/libvirt/storage/
    """
    path = "/etc/libvirt/storage/%s.xml" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))
    if not os.access(path, os.R_OK):
        return True
    else:
        return False

def undefine_pool(params):
    """Undefine a specific name storage pool"""
    global logger
    logger = params['logger']

    if not usage(params):
        return 1

    logger = params['logger']
    poolname = params['poolname']

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(virconn)

    if not check_pool_inactive(stgobj, poolname):
        return 1

    pool_num1 = stgobj.get_number_of_defpools()
    logger.info("original storage pool define number: %s" % pool_num1)
    display_pool_info(stgobj)

    try:
        logger.info("undefine %s storage pool" % poolname)
        stgobj.undefine_pool(poolname)
        pool_num2 = stgobj.get_number_of_defpools()
        logger.info("current storage pool define number: %s" % pool_num2)
        display_pool_info(stgobj)
        if check_pool_undefine(poolname) and pool_num2 < pool_num1:
            logger.info("undefine %s storage pool is successful" % poolname)
            return 0
        else:
            logger.error("%s storage pool is undefined" % poolname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
% (e.response()['message'], e.response()['code']))
        return 1
