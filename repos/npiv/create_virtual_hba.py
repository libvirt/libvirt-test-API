#!/usr/bin/env python
"""This test case is used for testing vHBA creating with npiv.
"""

__author__ = 'Neil Zhang: nzhang@redhat.com'
__date__ = 'Thu May 27, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'check_nodedev_create', 'check_nodedev_parent',
           'create_virtual_hba']

import os
import sys
import re
import commands
import xml.dom.minidom
from utils.Python import xmlbuilder

from lib import connectAPI
from lib import nodedevAPI
from utils.Python import utils
from exception import LibvirtAPI

def usage(params):
    """Verify input parameters"""

    keys = ['wwpn']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return False
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please input a value" %key)
            return False
        else:
            return True

def check_nodedev_create(wwpn, device_name):
    """Check if the node device vHBA was created. Can search created
       vport name in all FC list, to see if it exists.
    """

    pname_list = commands.getoutput("ls -1 -d /sys/class/*_host/host*/* \
                                     | grep port_name")
    for pname in pname_list.split("\n"):
        portid = open(pname).read()[2:].strip('\n')
        if wwpn == portid:
            logger.info("created virtual port name is %s" % portid)
            logger.info("The vHBA '%s' was created." % device_name)
            return True
        else:
            logger.info("No any virtual HBA was created")
            return False

def check_nodedev_parent(nodedev, device_parent, device_name):
    """Check created vHBA if its parent is correct. It's a bug 593995."""

    current_parent = nodedev.get_parent(device_name)
    if device_parent == current_parent:
        logger.info("The parent of node device '%s' is %s" \
                    % (device_name, current_parent))
        return True
    else:
        logger.info("Refer to bug 593995. The parent of node device \
                    '%s' is '%s'" % (device_name, current_parent))
        return False

def create_virtual_hba(params):
    """Create a vHBA with NPIV supported FC HBA."""

    global logger
    logger = params['logger']
    wwpn = params['wwpn']

    if not usage(params):
        return 1

    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    caps = conn.get_caps()
    logger.debug(caps)

    nodedev = nodedevAPI.NodedevAPI(conn)
    scsi_list = nodedev.lists('scsi_host')

    for fc_name in scsi_list:
        fc_xml = nodedev.dumpxml(fc_name)
        fc_cap = re.search('vport_ops', fc_xml)
        if fc_cap:
            params['parent'] = fc_name
            doc = xml.dom.minidom.parseString(fc_xml)
            wwnn_node = doc.getElementsByTagName('wwnn')[0]
            params['wwnn'] = wwnn_node.childNodes[0].nodeValue.encode('ascii', 'ignore')
            logger.info("NPIV support on '%s'" % fc_name)
            break
        else:
            logger.info("No NPIV capabilities on '%s'" % fc_name)

    xmlobj = xmlbuilder.XmlBuilder()
    nodedev_xml = xmlobj.build_nodedev(params)
    logger.debug("node device xml:\n%s" % nodedev_xml)

    try:
        try:
            logger.info("creating a virtual HBA ...")
            nodedev_obj = nodedev.create(nodedev_xml)
            dev_name = nodedev.get_name(nodedev_obj)

            if check_nodedev_create(wwpn, dev_name) and \
                check_nodedev_parent(nodedev, params['parent'], dev_name):
                logger.info("the virtual HBA '%s' was created successfully" \
                            % dev_name)
                return 0
            else:
                logger.error("fail to create the virtual HBA '%s'" \
                             % dev_name)
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("Error: fail to create %s virtual hba" % dev_name)
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
