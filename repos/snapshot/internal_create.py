#!/usr/bin/env python
""""virsh snapshot-create" testing
   mandatory arguments: guestname
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Sat Feb 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['internal_create', 'check_params', 'check_domain_image']

import os
import sys
import re
import time
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

from lib import connectAPI
from lib import snapshotAPI
from lib import domainAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

QEMU_IMAGE_FORMAT = "qemu-img info %s |grep format |awk -F': ' '{print $2}'" 

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    if params['guestname'] == "":
        logger.error("value of guestname is empty")
        return 1

    return 0

def check_domain_image(domobj, util, guestname, logger):
    """ensure that the state of guest is poweroff
       and its disk image is the type of qcow2
    """
    guest_names = domobj.get_defined_list()
    if guestname not in guest_names:
        logger.error("%s is not poweroff or doesn't exist" % guestname)
        return False
    else:
        dom_xml = domobj.get_xml_desc(guestname)
        disk_path = util.get_disk_path(dom_xml) 
        status, ret = commands.getstatusoutput(QEMU_IMAGE_FORMAT % disk_path)        
        if status:
            logger.error("executing "+ "\"" + QEMU_IMAGE_FORMAT % guestname + "\"" + " failed")
            logger.error(ret)
            return False
        else:
            format = ret
            if format == "qcow2":
                return True
            else:
                logger.error("%s has a disk %s with type %s, \
                              only qcow2 supports internal snapshot" % \
                              (guestname, disk_path, format))
                return False

def internal_create(params):
    """ create an internal snapshot for a given guest, 
        this case could be with other cases togerther to 
        check the functionality of snapshot
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1
    guestname = params['guestname']

    if not params.has_key('snapshotname'):
        params['snapshotname'] = str(int(time.time()))

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)
    snap_obj = snapshotAPI.SnapshotAPI(virconn)

    logger.info("checking domain and the format of its disk")
    if not check_domain_image(domobj, util, guestname, logger):
        logger.error("checking failed")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1
    
    xmlobj = xmlbuilder.XmlBuilder()
    snapshot_xml = xmlobj.build_domain_snapshot(params)
    logger.debug("%s snapshot xml:\n%s" % (guestname, snapshot_xml))

    try:
        logger.info("create a snapshot for %s" % guestname)
        snap_obj.create(guestname, snapshot_xml)
        logger.info("creating snapshot succeeded")
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
(e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0























