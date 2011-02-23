#!/usr/bin/evn python
"""this test case is used for testing
   virtual network start automatically capability
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Tue Mar 30, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'check_network_autostart', 'autostart']

import time
import os
import re
import sys
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

from lib.Python import connectAPI
from lib.Python import networkAPI
from utils.Python import utils
from exception import LibvirtAPI


def check_params(params):
    """Verify inputing parameter dictionary"""

    keys = ['networkname', 'autostart']
    for key in keys:
        if key not in params:
            logger.error("%s is required" % key)
            return 1

    return 0

def check_network_autostart(*args):
    """Check network start automatically result, if setting network is 
       successful, networkname.xml will exist under 
       /etc/libvirt/{hypervisor}/networks/autostart/
    """
    (networkname, hypervisor, flag, logger) = args
  
    netxml = "/etc/libvirt/%s/networks/autostart/%s.xml" % \
              (hypervisor, networkname)
    logger.debug("virtual network xml file is: %s" % netxml)

    if flag == 1:
        if os.access(netxml, os.F_OK):
            return True
        else:
            return False
    elif flag == 0:
        if not os.access(netxml, os.F_OK):
            return True
        else:
            return False
    else:
        return False

def autostart(params):
    """Set virtual network autostart capability"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if params_check_result:
        return 1

    networkname = params['networkname']
    autostart = params['autostart']
    
    test_result = False
    flag = -1

    if autostart == "enable":
        flag = 1
    elif autostart == "disable":
        flag = 0
    else:
        logger.error("Error: autostart value is invalid")
        return 1

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    logger.info("uri address is %s" % uri)

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    netobj = networkAPI.NetworkAPI(virconn)

    logger.debug("before setting autostart to virtual network, check status:")
    shell_cmd = "virsh net-list --all"
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug("the output of 'virsh net-list --all' is %s" % text)

    try:
        netobj.setnetAutostart(networkname, flag)
        if check_network_autostart(networkname, 
                                   "qemu", 
                                   flag, 
                                   logger):
            logger.info("current virtual network %s autostart: %s" % \
                         (networkname, netobj.get_autostart(networkname)))
            logger.info("executing autostart operation is successful")
            test_result = True
        else:
            logger.error("Error: fail to check autostart status of \
                          virtual network %s" % networkname)
            test_result = False
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to autostart virtual network %s " % \
                      networkname)
        test_result = False
        return 1

    logger.debug("After setting autostart to virtual network, check status:")
    shell_cmd = "virsh net-list --all"
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug("the output of 'virsh net-list --all' is %s" % text)
    time.sleep(3)
    if test_result:
        return 0
    else:
        return 1
