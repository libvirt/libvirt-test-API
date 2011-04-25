#!/usr/bin/env python
"""this test case is used for testing of building
   a disk type storage pool
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Thu June 03, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_pool_built', 'build_disk_pool', \
           'get_pool_devicename_type', 'check_pool_inactive',\
            'check_params']

import os
import re
import sys
import time
import commands
from xml.dom import minidom

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
from exception import LibvirtAPI

def usage():
    """usage information"""
    print """options:
              poolname: Name of pool to be built"""

def check_params(params):
    """Verify inputing parameter dictionary"""
    options = ['poolname']

    for option in options:
        if option not in params:
            logger.error("%s is required" % option)
            usage()
            return 1
        elif len(params[option]) == 0:
            logger.error("%s value is empty, please inputting a value" % option)
            return 1
        else:
            return 0

def check_pool_inactive(stgobj, poolname):
    """Check to make sure that the pool is defined and inactive"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names += stgobj.storage_pool_list()

    if poolname in pool_names:

        if stgobj.isActive_pool(poolname):
            logger.error("the %s storage pool is already active" % poolname)
            return False
        else:
            return True
    else:

        logger.error("the %s storage pool doesn't exist" % poolname)
        return False

def get_pool_devicename_type(stgobj, poolname):
    """ get device name and partition table of the pool
        from its xml description """
    poolxml = stgobj.dump_pool(poolname)

    logger.debug("the xml description of pool is %s" % poolxml)

    doc = minidom.parseString(poolxml)
    device_element = doc.getElementsByTagName('device')[0]
    source_device = device_element.attributes['path'].value

    format_element = doc.getElementsByTagName('format')[0]
    device_type = format_element.attributes['type'].value

    return source_device, device_type

def check_pool_built(source_device, device_type):
    """using parted command tool to check the validation of final result"""

    cmd = "parted -s %s print" % source_device
    ret, output = commands.getstatusoutput(cmd)
    partition_info = output.split("\n")[3]

    logger.debug("the partition information is %s" % partition_info)
    partition_table = partition_info.split(": ")[1]

    if device_type in partition_table:
        return 0
    else:
        return 1

def build_disk_pool(params):
    """ build a defined and inactive pool"""

    global logger
    logger = params['logger']

    params_check_result = check_params(params)

    if params_check_result:
        logger.error("parameters sanity check failed")
        return 1
    else:
        logger.info("parameters sanity check succeeded")

    poolname = params['poolname']
    logger.info("the poolname is %s" % (poolname))

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    stgobj = storageAPI.StorageAPI(virconn)

    logger.info("checking the state of given storage pool")
    if not check_pool_inactive(stgobj, poolname):
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    logger.info("checking storage pool state succeeded")

    source_device, device_type = get_pool_devicename_type(stgobj, poolname)
    logger.info("the source device of the pool is %s, \
                 the partition table type is %s" % \
                 (source_device, device_type))

    try:
        logger.info("begin to build the storage pool")
        stgobj.build_pool(poolname)
        time.sleep(5)
        if not check_pool_built(source_device, device_type):
            logger.info("building %s storage pool is SUCCESSFUL!!!" % poolname)
            return 0
        else:
            logger.info("building %s storage pool is UNSUCCESSFUL!!!" % \
                         poolname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
