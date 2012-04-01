#!/usr/bin/env python
"""
    Testcase to create a storage pool from an xml.
    Xml is built by this testcase by using the parameters.
"""

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils.Python import utils
from utils.Python import xmlbuilder

def usage(params):
    """ Verifies the params dictionary for the required arguments """
    logger = params['logger']
    # pooltype is optional, defaulted to "dir"
    # targetpath is optional, defaulted to /var/lib/libvirt/images
    keys = ['poolname']
    for key in keys:
        if key not in params:
            logger.error("%s parameter is required. \
                          Please set it to a value" % key)
            return False
        elif len(params[key]) == 0:
            logger.error("%s key is empty, set it to a value" % key)
            return False

    #optional keys:
    if "pooltype" not in params:
        params['pooltype'] = 'dir'

    # sanity check pooltype value:
    if params['pooltype'] == "dir":
        return True
    else:
        logger.error("pooltype parameter must be dir")
        logger.error("it is: %s" % params['pooltype'])


def check_pool_create(conn, poolname, logger):
    """Check the result of create storage pool.
    """
    pool_names = conn.listStoragePools()
    logger.info("poolnames is: %s " % pool_names)
    # check thru libvirt that it's really created..
    try:
        pool_names.index(poolname)
    except ValueError:
        logger.info("check_pool_create %s storage pool \
                     is UNSUCCESSFUL!!" % poolname)
        return False
    return True

def display_pool_info(conn, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % conn.listDefinedStoragePools())
    logger.debug("current active storage pool: %s" % conn.listStoragePools())

def create_dir_pool(params):
    """ Create a dir type storage pool from xml"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']
    pooltype = params['pooltype']

    util = utils.Utils()
    uri  = params['uri']

    conn = libvirt.open(uri)

    if check_pool_create(conn, poolname, logger):
        logger.error("%s storage pool has already been created" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    poolxml = xmlobj.build_pool(params)
    logger.debug("storage pool xml:\n%s" % poolxml)

    try:
        try:
            logger.info("Creating %s storage pool" % poolname)
            conn.storagePoolCreateXML(poolxml, 0)
            display_pool_info(conn, logger)
            if check_pool_create(conn, poolname, logger):
                logger.info("creating %s storage pool is SUCCESSFUL!!!" % poolname)
                return 0
            else:
                logger.info("aa creating %s storage pool is UNSUCCESSFUL!!!" % poolname)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
