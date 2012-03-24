#!/usr/bin/env python
"""
   This is a testcase used to define an iscsi based storage pool.
"""

__author__ = 'Gurhan Ozen gozen@redhat.com'
__date__ = 'Tue April 27, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'check_pool_define', \
           'display_pool_info', 'define_iscsi_pool']

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
    #targetpath is optional argument
    keys = ['poolname', 'pooltype', 'sourcename', 'sourcepath']
    for key in keys:
        if key not in params:
            logger.error("%s is required, targetpath is optional argument" %key)
            logger.info("please input the following argument:")
            logger.info(keys)
            return False
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return False

    if params['pooltype'] == "iscsi":
        return True
    else:
        logger.error("pooltype param must be iscsi")
        logger.error("it is: %s" % params['pooltype'])
        return False

def display_pool_info(stg, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def check_pool_define(storageobj, poolname, logger):
    """Check define storage pool result, if define storage is successful,
       poolname.xml will exist under /etc/libvirt/storage/
       and can use virt-xml-validate tool to check the file validity
    """
    path = "/etc/libvirt/storage/%s.xml" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))
    pool_names = storageobj.defstorage_pool_list()
    if os.access(path, os.R_OK):
        logger.debug("Check: %s does exist." % path)
        ## check thru libvirt that it's really defined..
        try:
            pool_names.index(poolname)
        except ValueError:
            logger.info("define %s storage pool is UNSUCCESSFUL!!" % poolname)
            return False
        return True
    else:
        return False

def define_iscsi_pool(params):
    """
    Defines a iscsi based storage pool from xml.
    Parameters passed are :
    pooltype, poolname, sourcename, sourcepath and targetpath.
    """
    logger = params['logger']
    if usage(params):
        logger.info("params are right")
    else:
        logger.info("params are wrong")
        return 1

    poolname = params['poolname']
    pooltype = params['pooltype']
    srcname = params['sourcename']
    srcpath = params['sourcepath']

    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(virconn)

    if check_pool_define(stgobj, poolname, logger):
        logger.error("%s storage pool is ALREADY defined" % poolname)
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
            if check_pool_define(stgobj, poolname, logger) and pool_num2 > pool_num1:
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
