#!/usr/bin/env python
"""testing "virsh hostname" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Jan 18, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['hostname']

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

VIRSH_HOSTNAME = "virsh hostname"

def hostname(params):
    """check virsh hostname command
    """
    logger = params['logger']

    status, virsh_ret = commands.getstatusoutput(VIRSH_HOSTNAME)
    if status:
        logger.error("executing " + "\"" + VIRSH_HOSTNAME + "\"" + " failed")
        return 1
    logger.info("the output of " + "\"" +  VIRSH_HOSTNAME + "\"" + " is %s" % virsh_ret)

    status, host_ret = commands.getstatusoutput("hostname")
    if status:
        logger.error("executing " + "\"" + "hostname" + "\"" + " failed")
        return 1

    if virsh_ret[:-1] != host_ret:
        logger.error("the output of " + VIRSH_HOSTNAME + " is not right" )
        return 1
    else:
        logger.info(VIRSH_HOSTNAME + " testing succeeded")

    return 0
