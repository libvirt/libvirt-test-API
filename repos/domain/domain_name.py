#!/usr/bin/env python
"""testing "virsh domname" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Jan 18, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['domname']

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

VIRSH_DOMNAME = "virsh domname"
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

def domname(params):
    """check virsh domname command
    """
    logger = params['logger']

    ids = []
    if 'domainid' in params:
        ids.append(params['domainid'])
    else:
        status, id_ret = get_output(logger, VIRSH_IDS)
        if not status:
            ids = id_ret.split('\n')
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

    id_domname = {}
    for id  in ids_list:
        index = ids_list.index(id)
        id_domname[id] = doms_list[index]

    for id in ids:
        status, domname_ret = get_output(logger, VIRSH_DOMNAME + " %s" % id)
        if status:
            return 1
        domname = domname_ret[:-1]
        if id_domname[id] == domname:
            logger.info("domid %s corresponds to guest %s" % (id, domname))
        else:
            logger.error("domid %s fails to match to guest %s" % (id, domname))
            return 1

    return 0
