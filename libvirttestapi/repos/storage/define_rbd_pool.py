# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# Define storage pool of 'rbd' type

from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.repos.storage import storage_common

required_params = ('poolname', 'cephserver', 'cephpool')
optional_params = {'xml': 'xmls/rbd_pool.xml'}


def define_rbd_pool(params):
    """Define a rbd type storage pool from xml"""
    logger = params['logger']
    poolname = params['poolname']
    server = params['cephserver']
    serverpool = params['cephpool']
    xmlstr = params['xml']

    try:
        conn = sharedmod.libvirtobj['conn']

        if not storage_common.check_pool(conn, poolname, logger):
            logger.error("%s storage pool is defined" % poolname)
            return 1

        logger.debug("storage pool xml:\n%s" % xmlstr)

        pool_num1 = conn.numOfDefinedStoragePools()
        logger.info("original storage pool define number: %s" % pool_num1)
        storage_common.display_pool_info(conn, logger)

        logger.info("define %s storage pool" % poolname)
        conn.storagePoolDefineXML(xmlstr, 0)
        pool_num2 = conn.numOfDefinedStoragePools()
        logger.info("current storage pool define number: %s" % pool_num2)
        storage_common.display_pool_info(conn, logger)
        if storage_common.check_pool_define(poolname, logger) and pool_num2 > pool_num1:
            logger.info("define %s storage pool is successful" % poolname)
        else:
            logger.error("%s storage pool is undefined" % poolname)
            return 1
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        return 1

    return 0


def define_rbd_pool_clean(params):
    logger = params['logger']
    poolname = params['poolname']

    conn = sharedmod.libvirtobj['conn']
    poolnames = conn.listDefinedStoragePools()
    if poolname in poolnames:
        poolobj = conn.storagePoolLookupByName(poolname)
        if poolobj.isActive():
            poolobj.destroy()
        else:
            poolobj.undefine()
