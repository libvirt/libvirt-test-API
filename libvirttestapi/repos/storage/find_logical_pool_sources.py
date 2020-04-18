# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# Test finding storage pool source of 'logical' type

from xml.dom import minidom
from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils

required_params = ('sourcepath',)
optional_params = {'xml': 'xmls/logical_pool.xml',
                   }


def check_pool_sources(xmlstr):
    """check the logical sources with command:
       pvs --noheadings -o pv_name,vg_name
    """
    source_val = {}
    source_cmp = {}

    doc = minidom.parseString(xmlstr)
    for diskTag in doc.getElementsByTagName("source"):
        name_element = diskTag.getElementsByTagName("name")[0]
        textnode = name_element.childNodes[0]
        name_val = textnode.data

        num = len(diskTag.getElementsByTagName("device"))
        for i in range(0, num):
            device_element = diskTag.getElementsByTagName("device")[i]
            attr = device_element.getAttributeNode('path')
            path_val = attr.nodeValue
            source_val.update({path_val: name_val, })

    logger.debug("pool source info dict is: %s" % source_val)

    cmd = "pvs -q --noheadings -o pv_name,vg_name | awk -F' ' '{print $1}'"
    ret, path_list = utils.exec_cmd(cmd, shell=True)

    cmd = "pvs -q --noheadings -o pv_name,vg_name | awk -F' ' '{print $2}'"
    ret, name_list = utils.exec_cmd(cmd, shell=True)

    for i in range(len(path_list)):
        source_cmp.update({path_list[i]: name_list[i]})

    logger.debug("pvs command output dict is: %s" % source_cmp)
    for key in source_cmp.copy():
        if not key.startswith('/dev/') and not key.startswith('[unknown]'):
            logger.debug("del %s: %s" % (key, source_cmp[key]))
            del source_cmp[key]

    if source_val == source_cmp:
        logger.info("source dict match with pvs command output")
        return 0
    else:
        logger.error("source dict did not match with pvs command output")
        return 1


def find_logical_pool_sources(params):
    """Find logical type storage pool sources from xml"""
    global logger
    logger = params['logger']
    sourcepath = params['sourcepath']
    xmlstr = params['xml']

    conn = sharedmod.libvirtobj['conn']
    try:

        logger.debug("storage source spec xml:\n%s" % xmlstr)

        logger.info("find pool sources of logical type")
        source_xml = conn.findStoragePoolSources('logical', xmlstr, 0)
        logger.info("pool sources xml description is:\n %s" % source_xml)

        ret = check_pool_sources(source_xml)
        if ret:
            logger.error("pool sources check failed")
            return 1
        else:
            logger.info("pool sources check succeed")

    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    return 0
