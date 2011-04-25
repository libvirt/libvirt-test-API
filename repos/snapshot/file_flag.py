#!/usr/bin/env python
""" create a flag file in the guest OS
   mandatory arguments: guestname, username, password
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Sat Feb 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['file_flag', 'check_params', 'check_domain_running']

import os
import sys
import re
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
from utils.Python import check
from exception import LibvirtAPI

FLAG_FILE = "snapshot_flag"
MAKE_FLAG = "rm -f /tmp/%s; touch /tmp/%s " % (FLAG_FILE, FLAG_FILE)

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname', 'username', 'password']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    return 0

def check_domain_running(domobj, guestname, logger):
    """ check if the domain exists and in running state as well """
    guest_names = domobj.get_list()

    if guestname not in guest_names:
        logger.error("%s is not running or does not exist" % guestname)
        return False
    else:
        return True

def make_flag(chk, ipaddr, username, password, logger):
    """ enter guest OS, create a file in /tmp folder """
    ret = chk.remote_exec_pexpect(ipaddr, username, password, MAKE_FLAG) 
    if ret == "TIMEOUT!!!":
        logger.error("connecting to guest OS timeout")
        return False
    elif ret != '':
        logger.error("failed to make flag in guest OS, %s" % ret)
        return False
    else:
        logger.info("flag %s is created in /tmp folder" % FLAG_FILE)
        return True 
              
def file_flag(params):
    """ create a new file in the /tmp folder of the guest
        as a flag 
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']        
    username = params['username']
    password = params['password']
 
    util = utils.Utils()
    chk = check.Check()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)

    if not check_domain_running(domobj, guestname, logger):
        logger.error("need a running guest")
        return return_close(conn, logger, 1)

    logger.info("get the mac address of vm %s" % guestname)
    mac = util.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 300
    while timeout:
        ipaddr = util.mac_to_ip(mac, 180)
        if not ipaddr:
            logger.info(str(timeout) + "s left")
            time.sleep(10)
            timeout -= 10
        else:
            logger.info("the ip address of vm %s is %s" % (guestname, ipaddr))
            break

    if timeout == 0:
        logger.info("vm %s failed to get ip address" % guestname)
        return return_close(conn, logger, 1)

    if not make_flag(chk, ipaddr, username, password, logger):
        logger.error("making flag in guest %s failed" % guestname)
        return return_close(conn, logger, 1)
    else:
        logger.info("making flag in guest %s succeeded" % guestname)
       
    return return_close(conn, logger, 0)
    
        

    

    



















