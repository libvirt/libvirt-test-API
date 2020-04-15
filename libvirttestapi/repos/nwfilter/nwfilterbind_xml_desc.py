import time
import lxml.etree

from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils

required_params = ('portdev',)
optional_params = {}


def nwfilterbind_xml_desc(params):
    logger = params['logger']
    portdev = params['portdev']
    logger.info("portdev: %s" % portdev)

    if not utils.version_compare("libvirt-python", 4, 5, 0, logger):
        logger.info("Current libvirt-python don't support nwfilterbind.XMLDesc().")
        return 0

    try:
        conn = sharedmod.libvirtobj['conn']
        nwfilterbind = conn.nwfilterBindingLookupByPortDev(portdev)
        xmldesc = nwfilterbind.XMLDesc()
        time.sleep(3)
        logger.info("get xml by api: %s" % xmldesc)

        tree = lxml.etree.fromstring(xmldesc)
        portdev_xml = tree.xpath('/filterbinding/portdev/@name')[0]
        logger.info("get port dev by xml: %s" % portdev_xml)
        if portdev_xml == portdev:
            logger.info("PASS: compare portdev successful.")
        else:
            logger.error("FAIL: compare portdev failed.")
            return 1

        filtername_xml = tree.xpath('/filterbinding/filterref/@filter')[0]
        logger.info("get filter name by xml: %s" % filtername_xml)
        filtername = nwfilterbind.filterName()
        logger.info("get filter name by api: %s" % filtername)
        if filtername_xml == filtername:
            logger.info("PASS: compare filter name successful.")
        else:
            logger.error("FAIL: compare filter name failed.")
            return 1
    except libvirtError as e:
        logger.error("API error message: %s" % e.get_error_message())
        return 1

    return 0
