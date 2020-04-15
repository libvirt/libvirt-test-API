# To test netfs type storage pool defining

from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.repos.storage import storage_common
from libvirttestapi.utils import process

required_params = ('poolname', 'sourcehost', 'sourcepath',)
optional_params = {'targetpath': '/tmp/netfs_test',
                   'xml': 'xmls/netfs_pool.xml',
                   }


def set_virt_use_nfs(logger):
    cmd = 'setsebool virt_use_nfs on'
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status != 0:
        logger.error("cmd failed: %s" % cmd)

    return 0


def define_netfs_pool(params):
    """Define a netfs type storage pool from xml"""
    logger = params['logger']
    poolname = params['poolname']
    xmlstr = params['xml']

    conn = sharedmod.libvirtobj['conn']

    if not storage_common.check_pool(conn, poolname, logger):
        logger.error("%s storage pool is defined" % poolname)
        return 1

    logger.debug("storage pool xml:\n%s" % xmlstr)

    set_virt_use_nfs(logger)

    pool_num1 = conn.numOfDefinedStoragePools()
    logger.info("original storage pool define number: %s" % pool_num1)
    storage_common.display_pool_info(conn, logger)

    try:
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
