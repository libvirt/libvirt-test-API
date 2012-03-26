#!/usr/bin/env python
"""this test case is used for testing define
   a logical type storage pool from xml
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu April 22, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_pool_define', \
           'display_pool_info', 'define_logical_pool']


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

from lib import connectAPI
from lib import storageAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    # Don't need to specify targetpath
    keys = ['poolname', 'pooltype', 'sourcename', 'sourcepath']
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

def display_pool_info(stg, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def check_pool_define(poolname, logger):
    """Check define storage pool result, if define storage is successful,
       poolname.xml will exist under /etc/libvirt/storage/
       and can use virt-xml-validate tool to check the file validity
    """
    path = "/etc/libvirt/storage/%s.xml" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))

    if os.access(path, os.R_OK):
        return True
    else:
        return False

def define_logical_pool(params):
    """Define a logical type storage pool from xml"""
    if not usage(params):
        return 1

    logger = params['logger']
    poolname = params['poolname']

    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(conn)

    if check_pool_define(poolname, logger):
        logger.error("%s storage pool is defined" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    poolxml = xmlobj.build_pool(params)
    logger.debug("storage pool xml:\n%s" % poolxml)

    pool_num1 = stgobj.get_number_of_defpools()
    logger.info("original storage pool define number: %s" % pool_num1)
    display_pool_info(stgobj, logger)

    try:
        try:
            logger.info("define %s storage pool" % poolname)
            stgobj.define_pool(poolxml)
            pool_num2 = stgobj.get_number_of_defpools()
            logger.info("current storage pool define number: %s" % pool_num2)
            display_pool_info(stgobj, logger)
            if check_pool_define(poolname, logger) and pool_num2 > pool_num1:
                logger.info("define %s storage pool is successful" % poolname)
                return 0
            else:
                logger.error("%s storage pool is undefined" % poolname)
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
