#!/usr/bin/env python
"""testing "virsh domid" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Jan 18, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['domid']

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

VIRSH_DOMID = "virsh domid"
VIRSH_IDS = "virsh --quiet list |awk '{print $1}'"
VIRSH_DOMS = "virsh --quiet list |awk '{print $2}'"

def get_output(logger, command):
    """execute shell command
    """
    status, ret = commands.getstatusoutput(command)
    if status:
        logger.error("executing "+ "\"" +  command  + "\"" + " failed")
        logger.error(ret)
    return status, ret

def domid(params):
    """check virsh domid command
    """
    logger = params['logger']

    doms = []
    if 'guestname' in params:
        doms.append(params['guestname'])
    else:
        status, doms_ret = get_output(logger, VIRSH_DOMS)
        if not status:
            doms = doms_ret.split('\n')
        else:
            return 1

    status, ids_ret = get_output(logger, VIRSH_IDS)
    if not status:
        ids_list = ids_ret.split('\n')
    else:
        return 1

    status, doms_ret = get_output(logger, VIRSH_DOMS)
    if not status:
        doms_list = doms_ret.split('\n')
    else:
        return 1

    domname_id = {}
    for dom  in doms_list:
        index = doms_list.index(dom)
        domname_id[dom] = ids_list[index]

    for dom in doms:
        status, domid_ret = get_output(logger, VIRSH_DOMID + " %s" % dom)
        if status:
            return 1
        domid = domid_ret[:-1]
        if domname_id[dom] == domid:
            logger.info("domname %s corresponds to id %s" % (dom, domid))
        else:
            logger.error("domname %s fails to match id %s" % (dom, domid))
            return 1

    return 0
