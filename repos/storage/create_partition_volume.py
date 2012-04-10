#!/usr/bin/env python
"""this test case is used for creating volume of
   a partition type storage pool from xml
"""

import os
import re
import sys
import commands

import libvirt
from libvirt import libvirtError

from utils import xmlbuilder

def usage():
    """usage infomation"""
    print """mandatory options:
              poolname: The name of pool under which the volume to be created
              volname: Name of the volume to be created
              volformat:  the format types of volume like \
                          'none,linux,fat16,fat32,linux-lvm...'
              capacity: the size of the volume with optional k,M,G,T suffix, \
                        for example '10G' """

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""

    mandatory_params = ['poolname', 'volname', 'volformat', 'capacity']

    for param in mandatory_params:
        if param not in params:
            logger.error("%s is required" % param)
            usage()
            return 1
        elif len(params[param]) == 0:
            logger.error("%s value is empty, please inputting a value" % param)
            return 1
        else:
            return 0

def partition_volume_check(poolobj, volname):
    """check the new created volume, the way of checking is to get
       the path of the newly created volume, then grep /proc/partitions
       to find out the new partition in that. """

    volobj = poolobj.storageVolLookupByName(volname)
    volpath = volobj.path()
    logger.debug("the path of volume is %s" % volpath)

    partition_name = volpath.split("/")[-1]
    shell_cmd = "grep %s /proc/partitions" % partition_name
    logger.debug("excute the shell command %s to \
                  check the newly created partition" % shell_cmd)

    stat, ret = commands.getstatusoutput(shell_cmd)

    if stat == 0 and volname in poolobj.listVolumes():
        return 0
    else:
        return 1


def virsh_vol_list(poolname):
    """using virsh command list the volume information"""

    shell_cmd = "virsh vol-list %s" % poolname
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug(text)


def create_partition_volume(params):
    """create a volume in the disk type of pool"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if not params_check_result:
        logger.info("Params are right")
    else:
        logger.error("Params are wrong")
        return 1

    poolname = params.pop('poolname')
    volname = params['volname']
    volformat = params['volformat']
    capacity = params.pop('capacity')

    logger.info("the poolname is %s, volname is %s, \
                 volfomat is %s, capacity is %s" % \
                 (poolname, volname, volformat, capacity))

    uri = params['uri']

    conn = libvirt.open(uri)

    storage_pool_list = conn.listStoragePools()

    if poolname not in storage_pool_list:
        logger.error("pool %s doesn't exist or not running")
        return return_close(conn, logger, 1)

    poolobj = conn.storagePoolLookupByName(poolname)

    params['suffix'] = capacity[-1]
    params['capacity'] = capacity[:-1]
    params['pooltype'] = 'disk'

    logger.info("before create the new volume, \
                 current volume list is %s" % \
                 poolobj.listVolumes())

    logger.info("and using virsh command to \
                 ouput the volume information in the pool %s" % poolname)
    virsh_vol_list(poolname)

    xmlobj = xmlbuilder.XmlBuilder()
    volumexml = xmlobj.build_volume(params)
    logger.debug("volume xml:\n%s" % volumexml)

    try:
        logger.info("create %s volume" % volname)
        poolobj.createXML(volumexml, 0)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                    % (e.message, e.get_error_code()))
        return return_close(conn, logger, 1)

    logger.info("volume create successfully, and output the volume information")
    virsh_vol_list(poolname)

    logger.info("Now, check the validation of the created volume")
    check_res = partition_volume_check(poolobj, volname)

    if not check_res:
        logger.info("checking succeed")
        return return_close(conn, logger, 0)
    else:
        logger.error("checking failed")
        return return_close(conn, logger, 1)
