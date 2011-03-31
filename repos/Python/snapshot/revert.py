#!/usr/bin/env python
""""virsh snapshot-revert" testing
   mandatory arguments: guestname snapshotname
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Sat Feb 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['revert', 'check_params', 'check_domain_state']

import os
import sys
import re

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
from lib.Python import snapshotAPI
from lib.Python import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname', 'snapshotname']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    return 0

def check_domain_state(domobj, guestname, logger):
    """ check if the domain exists and in shutdown state as well """
    guest_names = domobj.get_defined_list() 

    if guestname not in guest_names:
        logger.error("%s is running or does not exist" % guestname)
        return False
    else:
        return True

def revert(params):
    """ snapshot revert a snapshot for a given guest, 
        this case could be with other cases togerther to 
        check the functionality of snapshot
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']
    snapshotname = params['snapshotname']

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)
    snap_obj = snapshotAPI.SnapshotAPI(virconn)

    logger.info("checking if the guest is poweroff")
    if not check_domain_state(domobj, guestname, logger):
        logger.error("checking failed")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1
     
    try:
        logger.info("revert a snapshot for %s" % guestname)
        snap_obj.revertToSnapshot(guestname, snapshotname)
        logger.info("revert snapshot succeeded")
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
(e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0


