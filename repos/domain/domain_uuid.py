#!/usr/bin/env python
"""testing "virsh domuuid" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Jan 18, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['domuuid']

import os
import sys
import re
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
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

VIRSH_DOMUUID = "virsh domuuid"

def check_domain_exists(domobj, guestname, logger):
    """ check if the domain exists, may or may not be active """
    guest_names = domobj.get_list()
    guest_names += domobj.get_defined_list()

    if guestname not in guest_names:
        logger.error("%s doesn't exist" % guestname)
        return False
    else:
        return True

def check_domain_uuid(guestname, UUIDString, logger):
    """ check UUID String of guest """
    status, ret = commands.getstatusoutput(VIRSH_DOMUUID + ' %s' % guestname)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_DOMUUID + ' %s' % guestname + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        UUIDString_virsh = ret[:-1]
        logger.debug("UUIDString from API is %s" % UUIDString)
        logger.debug("UUIDString from virsh domuuid is %s" % UUIDString_virsh)
        if UUIDString == ret[:-1]:
            return True
        else:
            return False

def domuuid(params):
    """check virsh domuuid command
    """
    logger = params['logger']

    if 'guestname' not in params:
        logger.error("option guestname is required")
        return 1
    else:
        guestname = params['guestname']
        logger.info("guest name is %s" % guestname)

    util = utils.Utils()
    uri = params['uri']
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)

    if not check_domain_exists(domobj, guestname, logger):
        logger.error("need a defined guest, may or may not be active")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    try:
        try:
            logger.info("get the UUID string of %s" % guestname)
            UUIDString = domobj.get_uuid_string(guestname)
            if check_domain_uuid(guestname, UUIDString, logger):
                logger.info("UUIDString from API is the same as the one from virsh")
                logger.info("UUID String is %s" % UUIDString)
                return 0
            else:
                logger.error("UUIDString from API is not the same as the one from virsh")
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" % \
                         (e.response()['message'], e.response()['code']))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")
