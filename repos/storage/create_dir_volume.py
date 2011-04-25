#!/usr/bin/env python
"""this test case is used for creating volume of
   a dir type storage pool from xml
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Thu May 6, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_params', \
           'get_pool_path', 'dir_volume_check', 'create_dir_volume']


import os
import re
import sys
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

from lib.Python import connectAPI
from lib.Python import storageAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage():
    """usage infomation"""
    print """mandatory options:
              poolname: The name of pool under which the volume to be created
              volname: Name of the volume to be created
              volformat:  the format types of volume like 'raw, qcow, qcow2'
              capacity: the size of the volume with optional k,M,G,T suffix,
              for example '10G' """

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
            pass

def get_pool_path(stgobj, poolname):
    """ get pool xml description """
    poolxml = stgobj.dump_pool(poolname)

    logger.debug("the xml description of pool is %s" % poolxml)

    doc = minidom.parseString(poolxml)
    path_element = doc.getElementsByTagName('path')[0]
    textnode = path_element.childNodes[0]
    path_value = textnode.data

    return path_value

def dir_volume_check(volume_path, capacity, volformat):
    """check the new created volume """
    unit_bytes = {'K':pow(2, 10), 'M':pow(2, 20), \
                  'G':pow(2, 30), 'T':pow(2, 40)}

    if os.path.exists(volume_path):
        shell_cmd = "qemu-img info %s" % volume_path
        res, text = commands.getstatusoutput(shell_cmd)

        logger.debug("the output of qemu-img is %s" % text)

        format_info = text.split('\n')[1]
        disk_info = text.split('\n')[2]

        actual_format = format_info.split(": ")[1]
        actual_size_bytes = disk_info.split("(")[1].split(" ")[0]

        expected_size_bytes = unit_bytes[capacity[-1]] * int(capacity[:-1])

        logger.debug("the actual_size_bytes is %s, \
                      the expected_size_bytes is %s" % \
                      (actual_size_bytes, expected_size_bytes))
        logger.debug("the actual_format is %s, the expected_format is %s" % \
                      (actual_format, volformat))

        if int(actual_size_bytes) == expected_size_bytes and \
                actual_format == volformat:
            return 0
        else:
            return 1

    else:
        logger.error("volume file %s doesn't exist" % volume_path)
        return 1

def virsh_vol_list(poolname):
    """using virsh command list the volume information"""

    shell_cmd = "virsh vol-list %s" % poolname
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug(text)


def create_dir_volume(params):
    """create a volume in the dir type of pool"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if params_check_result:
        return 1

    poolname = params.pop('poolname')
    volname = params['volname']
    volformat = params['volformat']
    capacity = params.pop('capacity')

    logger.info("the poolname is %s, volname is %s, \
                 volfomat is %s, capacity is %s" % \
                (poolname, volname, volformat, capacity))

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    stgobj = storageAPI.StorageAPI(virconn)

    storage_pool_list = stgobj.storage_pool_list()

    if poolname not in storage_pool_list:
        logger.error("pool %s doesn't exist or not running")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    path_value = get_pool_path(stgobj, poolname)

    volume_path = path_value + "/" + volname

    params['volpath'] = volume_path
    params['suffix'] = capacity[-1]
    params['capacity'] = capacity[:-1]
    params['pooltype'] = 'dir'

    logger.info("before create the new volume, current volume list is %s" % \
                 stgobj.get_volume_list(poolname))

    logger.info("and using virsh command to ouput \
                 the volume information in the pool %s" % poolname)
    virsh_vol_list(poolname)

    xmlobj = xmlbuilder.XmlBuilder()
    volumexml = xmlobj.build_volume(params)
    logger.debug("volume xml:\n%s" % volumexml)

    try:
        logger.info("create %s volume" % volname)
        stgobj.create_volume(poolname, volumexml)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    logger.info("volume create successfully, and output the volume information")
    virsh_vol_list(poolname)

    logger.info("Now, let check the validation of the created volume")
    check_res = dir_volume_check(volume_path, capacity, volformat)

    if check_res:
        logger.error("checking failed")
        return 1
    else:
        logger.info("checking succeed")

    return 0
