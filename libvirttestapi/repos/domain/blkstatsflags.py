# To test domain block device statistics with flags

import time
import libvirt

from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.utils.utils import get_xml_value

required_params = ('guestname', 'flags')
optional_params = {}


def check_guest_status(domobj):
    """Check guest current status"""
    state = domobj.info()[0]
    if state == libvirt.VIR_DOMAIN_SHUTOFF or \
            state == libvirt.VIR_DOMAIN_SHUTDOWN:
        # add check function
        return False
    else:
        return True


def check_blkstats():
    """Check block device statistic result"""
    pass


def blkstatsflags(params):
    """Domain block device statistic"""
    logger = params['logger']
    guestname = params['guestname']
    flags = int(params['flags'])

    conn = sharedmod.libvirtobj['conn']

    domobj = conn.lookupByName(guestname)

    # Check domain block status
    if check_guest_status(domobj):
        pass
    else:
        domobj.create()
        time.sleep(90)
    try:
        xml_path = "/domain/devices/disk/target/@dev"
        devs = get_xml_value(domobj, xml_path)
        for dev in devs:
            blkstats = domobj.blockStatsFlags(dev, flags)
            # check_blkstats()
            logger.debug(blkstats)
            for entry in list(blkstats.keys()):
                logger.info("%s %s %s" % (dev, entry, blkstats[entry]))

    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        return 1

    return 0
