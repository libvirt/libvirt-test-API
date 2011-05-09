#!/usr/bin/env python
"""this test case is used for testing create
   a logical type storage volume from xml
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu May 20, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_volume_create', 'check_pool_inactive', \
           'display_volume_info', 'create_logical_volume']


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

from lib import connectAPI
from lib import storageAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage(params):
    """Verify inputing parameter dictionary"""
    #  'allocation' is optional
    keys = ['poolname', 'pooltype', 'volname', 'capacity']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            logger.info("please input the following argument:")
            logger.info(keys)
            return False
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return False
        else:
            return True

def get_pool_path(stgobj, poolname):
    """ Get pool target path """
    poolxml = stgobj.dump_pool(poolname)

    logger.debug("the xml description of pool is %s" % poolxml)

    doc = minidom.parseString(poolxml)
    path_element = doc.getElementsByTagName('path')[0]
    textnode = path_element.childNodes[0]
    return textnode.data

def display_volume_info(stg, poolname):
    """Display current storage volume information"""
    logger.debug("current created storage volume: %s" \
% stg.get_volume_list(poolname))

def display_physical_volume():
    """Display current physical volume information"""
    stat, ret = commands.getstatusoutput("lvdisplay")
    logger.debug("lvdisplay command execute return value: %d" % stat)
    logger.debug("lvdisplay command execute return result: %s" % ret)

def get_storage_volume_number(stgobj, poolname):
    """Get storage volume number"""
    vol_num = stgobj.get_volume_number(poolname)
    logger.info("current storage volume number: %s" % vol_num)
    return vol_num

def check_pool_active(stgobj, poolname):
    """Check to make sure that the pool is active"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names += stgobj.storage_pool_list()
    if poolname in pool_names:
        if stgobj.isActive_pool(poolname):
            return True
        else:
            logger.error("%s pool is inactive" % poolname)
            return False
    else:
        logger.error("%s pool don't exist" % poolname)
        return False

def check_volume_create(stg, poolname, volname, size):
    """Check storage volume result, poolname will exist under
       /etc/lvm/backup/ and lvcreate command is called if
       volume creation is successful
    """
    path = "/etc/lvm/backup/%s" % poolname
    logger.debug("%s file path: %s" % (poolname, path))
    if os.access(path, os.R_OK):
        logger.debug("execute grep lvcreate %s command" % path)
        stat, ret = commands.getstatusoutput("grep \
'lvcreate --name %s -L %sK /dev/%s' %s"\
 % (volname, size, poolname, path))
        if stat == 0 and volname in stg.get_volume_list(poolname):
            logger.debug(ret)
            return True
        else:
            logger.debug(ret)
            return False
    else:
        logger.debug("%s file don't exist" % path)
        return False

def create_logical_volume(params):
    """Create a logical type storage volume from xml"""
    global logger
    logger = params['logger']

    if not usage(params):
        return 1

    poolname = params['poolname']
    volname = params['volname']
    capacity = params['capacity']

    util = utils.Utils()
    dicts = util.get_capacity_suffix_size(capacity)

    params['capacity'] = dicts['capacity']
    params['suffix'] = dicts['suffix']
    # default is KB in the /etc/lvm/backup/{poolname}
    caps_kbyte = dicts['capacity_byte']/1024

    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(virconn)

    # active pool can create volume
    if not check_pool_active(stgobj, poolname):
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    poolpath = get_pool_path(stgobj, poolname)
    logger.debug("pool target path: %s" % poolpath)
    params['volpath'] = "%s/%s" % (poolpath, volname)
    logger.debug("volume target path: %s" % params['volpath'])

    xmlobj = xmlbuilder.XmlBuilder()
    volxml = xmlobj.build_volume(params)
    logger.debug("storage volume xml:\n%s" % volxml)

    vol_num1 = get_storage_volume_number(stgobj, poolname)
    display_volume_info(stgobj, poolname)
    display_physical_volume()

    try:
        logger.info("create %s storage volume" % volname)
        stgobj.create_volume(poolname, volxml)
        display_physical_volume()
        vol_num2 = get_storage_volume_number(stgobj, poolname)
        display_volume_info(stgobj, poolname)
        if check_volume_create(stgobj, poolname, volname, caps_kbyte) \
            and vol_num2 > vol_num1:
            logger.info("create %s storage volume is successful" % volname)
            return 0
        else:
            logger.error("fail to crearte %s storage volume" % volname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
