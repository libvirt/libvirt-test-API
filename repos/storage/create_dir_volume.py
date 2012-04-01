#!/usr/bin/env python
"""this test case is used for creating volume of
   a dir type storage pool from xml
"""

import os
import re
import sys
import commands
from xml.dom import minidom

import libvirt
from libvirt import libvirtError

from utils.Python import utils
from utils.Python import xmlbuilder

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

def get_pool_path(poolobj):
    """ get pool xml description """
    poolxml = poolobj.XMLDesc(0)

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
    uri = params['uri']

    conn = libvirt.open(uri)
    storage_pool_list = conn.listStoragePools()

    if poolname not in storage_pool_list:
        logger.error("pool %s doesn't exist or not running")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    poolobj = conn.storagePoolLookupByName(poolname)

    path_value = get_pool_path(poolobj)

    volume_path = path_value + "/" + volname

    params['volpath'] = volume_path
    params['suffix'] = capacity[-1]
    params['capacity'] = capacity[:-1]
    params['pooltype'] = 'dir'

    logger.info("before create the new volume, current volume list is %s" % \
                 poolobj.listVolumes())

    logger.info("and using virsh command to ouput \
                 the volume information in the pool %s" % poolname)
    virsh_vol_list(poolname)

    xmlobj = xmlbuilder.XmlBuilder()
    volumexml = xmlobj.build_volume(params)
    logger.debug("volume xml:\n%s" % volumexml)

    try:
        try:
            logger.info("create %s volume" % volname)
            poolobj.createXML(volumexml, 0)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))

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
