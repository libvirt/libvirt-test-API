#!/usr/bin/env python

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import xmlbuilder

required_params = ('poolname',)
optional_params = ()

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_pool_destroy(conn, poolname, logger):
    """
     Check to verify that the pool is actually gone
    """
    pool_names = conn.listStoragePools()

    if poolname not in pool_names:
        logger.info("destroy pool %s SUCCESS , " % poolname)
        logger.info("%s doesn't seem to be an active poolname anymore, " % \
                     poolname)
        return True
    else:
        logger.error("destroy pool %s UNSUCCESSFUL" % poolname)
        logger.error("%s is still in the list after destroy" % poolname)
        return True

def destroy_pool(params):
    """Function to actually destroy the pool"""
    logger = params['logger']
    poolname = params['poolname']
    uri = params['uri']
    conn = libvirt.open(uri)

    pool_names = conn.listDefinedStoragePools()
    pool_names += conn.listStoragePools()

    if poolname in pool_names:
        poolobj = conn.storagePoolLookupByName(poolname)
    else:
        logger.error("%s not found\n" % poolname);
        conn.close()
        return 1

    if not poolobj.isActive():
        logger.error("%s is not active. \
                          It must be active to be destroyed." % poolname)
        return return_close(conn, logger, 1)

    try:
        poolobj.destroy()
        # Check in libvirt to make sure that it's really destroyed..
        if not check_pool_destroy(conn, poolname, logger):
            logger.error("%s doesn't seem to be destroyed properly" % poolname)
            return return_close(conn, logger, 1)
        else:
            logger.info("%s is destroyed!!!" % poolname)
            return return_close(conn, logger, 0)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                    % (e.message, e.get_error_code()))
        return return_close(conn, logger, 1)
