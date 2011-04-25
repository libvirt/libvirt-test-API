#!/usr/bin/env python
"""this test case is used for testing build
   a dir type storage pool
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Fri May 28, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_build_pool', 'build_dir_pool', \
           'display_pool_info', 'check_pool_defined']


import os
import re
import sys
import commands
from xml.dom import minidom

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib import connectAPI
from lib import storageAPI
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

def check_pool_defined(stgobj, poolname):
    """Check to make sure that the pool is defined"""
    pool_names = stgobj.defstorage_pool_list()
    if poolname in pool_names:
        logger.debug("the pool %s is defined " %poolname)
        return True
    else:
        logger.error("the pool %s is active or undefine" % poolname)
        return False

def check_build_pool(path):
    """Check poolname directory if exist, it will exist
       directory if the directory has ever be created or
       pool building is successful
    """
    if os.access(path, os.R_OK):
        logger.debug("%s directory is existent" % path)
        return True
    else:
        logger.debug("%s directory don't exist" % path)
        return False

def build_dir_pool(params):
    """Build a storage pool"""
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

    if not check_pool_defined(stgobj, poolname):
        logger.error("only have defined pool can be built")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    pool_xml = stgobj.dump_pool(poolname)
    doc = minidom.parseString(pool_xml)
    unicode_path_value = doc.getElementsByTagName("path")[0].firstChild.data
    path_value = unicode_path_value.encode()

    if check_build_pool(path_value):
        logger.debug("%s directory has be built" % path_value)

    display_pool_info(stgobj)

    try:
        logger.info("build %s storage pool" % poolname)
        stgobj.build_pool(poolname)
        display_pool_info(stgobj)

        if check_build_pool(path_value):
            logger.info("build %s storage pool is successful" % poolname)
            return 0
        else:
            logger.error("fail to build %s storage pool" % poolname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0

def build_dir_pool_clean(params):
    pass
