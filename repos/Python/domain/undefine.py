#!/usr/bin/evn python
"""this test case is used for testing
   undefine domain
   mandatory arguments: guestname
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu Feb 11, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_undefine_domain', 'undefine']

import os
import re
import sys

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

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1

def check_undefine_domain(guestname):
    """Check undefine domain result, if undefine domain is successful,
       guestname.xml will don't exist under /etc/libvirt/qemu/
    """
    path = "/etc/libvirt/qemu/%s.xml" % guestname
    if not os.access(path, os.R_OK):
        return True
    else:
        return False

def undefine(params):
    """Undefine a domain"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    # Get capability debug info
    caps = conn.get_caps()
    logger.debug(caps)

    # Undefine domain
    dom_obj = domainAPI.DomainAPI(virconn)

    try:
        dom_obj.undefine(guestname)
        if  check_undefine_domain(guestname):
            logger.info("undefine the domain is successful")
            test_result = True
        else:
            logger.error("fail to check domain undefine")
            test_result = False
    except:
        logger.error("fail to undefine the domain")
        test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1
