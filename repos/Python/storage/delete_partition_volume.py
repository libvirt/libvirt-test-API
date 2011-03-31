#!/usr/bin/env python
"""this test case is used for deleting volume of
   a partition type storage pool from xml
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Thu May 19, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_params', \
           'partition_volume_check', 'delete_partition_volume']


import os
import re
import sys
import commands

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib.Python import connectAPI
from lib.Python import storageAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage():
    """usage infomation"""
    print """mandatory options:
              poolname: The name of pool under which the volume to be created
              volname: Name of the volume to be created"""

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""

    mandatory_params = ['poolname', 'volname']

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

def partition_volume_check(stgobj, poolname, volname, partition_name):
    """check the newly deleted volume, the way of checking is to
       grep the partition name of the volume in /proc/partitions
       to ensure its non-existence"""

    shell_cmd = "grep %s /proc/partitions" % partition_name
    logger.debug("excute the shell command %s to \
                  check the newly created partition" % shell_cmd)

    stat, ret = commands.getstatusoutput(shell_cmd)

    if stat != 0 and volname not in stgobj.get_volume_list(poolname):
        return 0
    else:
        return 1

def virsh_vol_list(poolname):
    """using virsh command list the volume information"""

    shell_cmd = "virsh vol-list %s" % poolname
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug(text)


def delete_partition_volume(params):
    """delete a volume in the disk type of pool"""

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

    logger.info("the poolname is %s, volname is %s" % (poolname, volname))

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    stgobj = storageAPI.StorageAPI(virconn)

    storage_pool_list = stgobj.storage_pool_list()

    if poolname not in storage_pool_list:
        logger.error("pool %s doesn't exist or not running")
        return return_close(conn, logger, 1)

    logger.info("before deleting a volume, \
                 current volume list in the pool %s is %s" % \
                 (poolname, stgobj.get_volume_list(poolname)))

    logger.info("and using virsh command to \
                 ouput the volume information in the pool %s" % poolname)
    virsh_vol_list(poolname)

    volpath = stgobj.get_volume_path(poolname, volname)
    logger.debug("the path of volume is %s" % volpath)

    partition_name = volpath.split("/")[-1]

    try:
        logger.info("delete volume %s" % volname)
        stgobj.delete_volume(poolname, volname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
% (e.response()['message'], e.response()['code']))
        return return_close(conn, logger, 1)

    logger.info("delete volume successfully, and output the volume information")
    logger.info("after deleting a volume, \
                 current volume list in the pool %s is %s" % \
                 (poolname, stgobj.get_volume_list(poolname)))
    virsh_vol_list(poolname)

    logger.info("Now, check the validation of deleting volume")
    check_res = partition_volume_check(stgobj, poolname, \
                                       volname, partition_name)

    if not check_res:
        logger.info("checking succeed")
        return return_close(conn, logger, 0)
    else:
        logger.error("checking failed")
        return return_close(conn, logger, 1)
