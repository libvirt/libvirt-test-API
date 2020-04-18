# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# Test finding storage pool source of 'iscsi' type

from xml.dom import minidom
from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils

required_params = ('sourcehost',)
optional_params = {'xml': 'xmls/iscsi_pool_source.xml',
                   }


def check_pool_sources(host, xmlstr):
    """check the iscsi sources with command:
       iscsiadm --mode discovery --type sendtargets --portal
    """
    source_val = []

    doc = minidom.parseString(xmlstr)
    for diskTag in doc.getElementsByTagName("source"):
        device_element = diskTag.getElementsByTagName("device")[0]
        attr = device_element.getAttributeNode('path')
        path_val = attr.nodeValue

        source_val.append(path_val)

    logger.debug("pool source info list is: %s" % source_val)

    cmd = "iscsiadm --mode discovery --type sendtargets --portal %s:3260,1 |\
           awk -F' ' '{print $2}'" % host
    ret, path_list = utils.exec_cmd(cmd, shell=True)

    logger.debug("iscsiadm command output list is: %s" % path_list)

    if source_val == path_list:
        logger.info("source list matched with iscsiadm command output")
        return 0
    else:
        logger.error("source list did not match with iscsiadm command output")
        return 1


def find_iscsi_pool_sources(params):
    """Find iscsi type storage pool sources from xml"""
    global logger
    logger = params['logger']
    sourcehost = params['sourcehost']
    xmlstr = params['xml']

    conn = sharedmod.libvirtobj['conn']
    try:

        logger.debug("storage source spec xml:\n%s" % xmlstr)

        logger.info("find pool sources of iscsi type")
        source_xml = conn.findStoragePoolSources('iscsi', xmlstr, 0)
        logger.info("pool sources xml description is:\n %s" % source_xml)

        ret = check_pool_sources(sourcehost, source_xml)
        if ret:
            logger.error("pool sources check failed")
            return 1
        else:
            logger.info("pool sources check succeed")

    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    return 0
