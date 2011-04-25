#!/usr/bin/env python
"""
    Testcase to create a filesystem based storage pool from an xml.
    Xml is built by this testcase by using the parameters.
"""

__author__   = 'Gurhan Ozen: gozen@redhat.com'
__date__     = 'Fri April 30, 2010'
__version__  = '0.1.0'
__credits__  = 'Copyright (C) 2010 Red Hat, Inc.'
__all__      = ['usage', 'check_pool_create', 'create_fs_pool']

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
from utils.Python import XMLParser
from exception import LibvirtAPI

def usage(params):
    """ Verifies the params dictionary for the required arguments """
    logger = params['logger']
    # targetpath is optional
    keys = ['poolname', 'sourcepath', 'pooltype']
    for key in keys:
        if key not in params:
            logger.error("%s parameter is required. \
                          Please set it to a value" % key)
            return False
        elif len(params[key]) == 0:
            logger.error("%s key is empty, set it to a value" % key)
            return False

    # inform the tester about the default format value...
    if "sourceformat" not in params:
        logger.info("The sourceformat parameter is not given. Default value of \
                     ext3 will be used")

    # sanity check pooltype value:
    if params['pooltype'] == "fs":
        return True
    else:
        logger.error("pooltype parameter must be fs")
        logger.error("it is: %s" % params['pooltype'])

def check_pool_exists(stgobj, poolname, logger):
    """ Check to see if the pool exists """
    pool_names = stgobj.storage_pool_list()
    pool_names += stgobj.defstorage_pool_list()
    logger.info("poolnames is: %s " % pool_names)

    if poolname in pool_names:
        return True
    else:
        return False

def check_pool_create_libvirt(stgobj, poolname, logger):
    """Check the result of create storage pool on libvirt level.  """
    pool_names = stgobj.storage_pool_list()
    logger.info("poolnames is: %s " % pool_names)
    # check thru libvirt that it's really created..
    if poolname in pool_names:
        return True
    else:
        logger.info("check_pool_create %s storage pool \
                     doesn't exist in libvirt!!!!" % poolname)
        return False

def check_pool_create_OS(stgobj, poolname, logger):
    """Check the result of create storage pool on OS level.  """
    poolxml = stgobj.dump_pool(poolname)
    out = XMLParser.XMLParser().parse(poolxml)
    src_path = out["source"]["device"]["attr"]["path"]
    dest_path = out["target"]["path"]
    logger.info("src path: %s tgt path: %s" % (src_path, dest_path))
    pat = src_path + "\s+" + dest_path
    found = 0
    fd = open("/proc/mounts","r")
    for line in fd:
        if re.match(pat, line):
            found = 1
    fd.close()
    if found:
        return True
    else:
        return False

def display_pool_info(stg, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def create_fs_pool(params):
    """ Create a fs type storage pool from xml"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']

    util = utils.Utils()
    uri  = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    caps = conn.get_caps()
    logger.debug(caps)
    stgobj = storageAPI.StorageAPI(virconn)

    if check_pool_exists(stgobj, poolname, logger):
        logger.error("%s storage pool has already been created" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    poolxml = xmlobj.build_pool(params)
    logger.debug("storage pool xml:\n%s" % poolxml)

    try:
        logger.info("Creating %s storage pool" % poolname)
        stgobj.create_pool(poolxml)
        display_pool_info(stgobj, logger)
        if check_pool_create_libvirt(stgobj, poolname, logger):
            logger.info("creating %s storage pool is in libvirt" % poolname)
            if check_pool_create_OS(stgobj, poolname, logger):
                logger.info("creating %s storage pool is SUCCESSFUL!!!" % poolname)
                return 0
            else:
                logger.info("creating %s storage pool is UNSUCCESSFUL!!!" % \
                             poolname)
                return 1
        else:
            logger.info("creating %s storage pool is \
                         UNSUCCESSFUL in libvirt!!!" % poolname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
