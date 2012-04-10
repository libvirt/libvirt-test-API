#!/usr/bin/env python
"""
    Testcase to create a filesystem based storage pool from an xml.
    Xml is built by this testcase by using the parameters.
"""

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import xmlbuilder
from utils import XMLParser

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

def check_pool_create_libvirt(conn, poolname, logger):
    """Check the result of create storage pool on libvirt level.  """
    pool_names = conn.listStoragePools()
    logger.info("poolnames is: %s " % pool_names)
    # check thru libvirt that it's really created..
    if poolname in pool_names:
        return True
    else:
        logger.info("check_pool_create %s storage pool \
                     doesn't exist in libvirt!!!!" % poolname)
        return False

def check_pool_create_OS(poolobj, logger):
    """Check the result of create storage pool on OS level.  """
    poolxml = poolobj.XMLDesc(0)
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

def display_pool_info(conn, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % conn.listDefinedStoragePools())
    logger.debug("current active storage pool: %s" % conn.listStoragePools())

def create_fs_pool(params):
    """ Create a fs type storage pool from xml"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']

    uri  = params['uri']

    conn = libvirt.open(uri)
    pool_names = conn.listDefinedStoragePools()
    pool_names += conn.listStoragePools()

    if poolname in pool_names:
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
            poolobj = conn.storagePoolCreateXML(poolxml, 0)
            display_pool_info(conn, logger)
            if check_pool_create_libvirt(conn, poolname, logger):
                logger.info("creating %s storage pool is in libvirt" % poolname)
                if check_pool_create_OS(poolobj, logger):
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
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
