#!/usr/bin/env python
"""this test case is used for testing detach
   the disk to domain from xml
   mandatory arguments: guestname
                        guesttype
                        imagename
                        hdmodel
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Mon Jan 28, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_detach_disk',
           'detach_disk']

import os
import re
import sys
import time

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
from lib.Python import domainAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'guesttype', 'imagename', 'hdmodel']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1

def check_guest_status(guestname, domobj):
    """Check guest current status"""
    state = domobj.get_state(guestname)
    if state == "shutoff" or state == "shutdown":
    # add check function
        return False
    else:
        return True

def check_detach_disk(num1, num2):
    """Check detach disk result via simple disk number
       comparison
    """
    if num2 < num1:
        return True
    else:
        return False

def detach_disk(params):
    """Detach a disk to domain from xml"""
     # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    imagename = params['imagename']
    disktype = params['hdmodel']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    # Detach disk
    domobj = domainAPI.DomainAPI(virconn)
    xmlobj = xmlbuilder.XmlBuilder()
    diskxml = xmlobj.build_disk(params)
    logger.debug("disk xml:\n%s" %diskxml)

    disk_num1 = util.dev_num(guestname, "disk")
    logger.debug("original disk number: %s" %disk_num1)

    if disktype == "virtio":
        if check_guest_status(guestname, domobj):
            pass
        else:
            domobj.start(guestname)
            time.sleep(90)

    try:
        domobj.detach_device(guestname, diskxml)
        disk_num2 = util.dev_num(guestname, "disk")
        logger.debug("update disk number to %s" %disk_num2)
        if  check_detach_disk(disk_num1, disk_num2):
            logger.info("current disk number: %s\n" %disk_num2)
            test_result = True
        else:
            logger.error("fail to detach a disk to guest: %s\n" %disk_num2)
            test_result = False
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("detach %s disk from guest %s" % (imagename, guestname))
        test_result = False
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1

def detach_disk_clean(params):
    """ clean testing environment """
    pass
