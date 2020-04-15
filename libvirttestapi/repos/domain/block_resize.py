# To test domain block device resize

import time
import libvirt
from libvirt import libvirtError

from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils

required_params = ('guestname', 'diskpath', 'disksize',)
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


def block_resize(params):
    """domain block resize test function
    """
    logger = params['logger']
    guestname = params['guestname']
    diskpath = params['diskpath']
    disksize = params['disksize']
    flag = 0

    out = utils.get_capacity_suffix_size(disksize)
    if len(out) == 0:
        logger.error("disksize parse error: \'%s\'" % disksize)
        logger.error("disksize should be a number with capacity suffix")
        return 1

    if out['suffix'] == 'K':
        flag = 0
        disksize = int(out['capacity'])
    elif out['suffix'] == 'B':
        flag = 1
        disksize = int(out['capacity_byte'])
    elif out['suffix'] == 'M':
        flag = 0
        disksize = int(out['capacity']) * 1024
    elif out['suffix'] == 'G':
        flag = 0
        disksize = int(out['capacity']) * 1024 * 1024
    else:
        logger.error("disksize parse error: with a unsupported suffix \'%s\'"
                     % out['suffix'])
        logger.error("the available disksize suffix of block_resize is: ")
        logger.error("B, K, M, G, T")
        return 1

    conn = sharedmod.libvirtobj['conn']

    domobj = conn.lookupByName(guestname)

    # Check domain block status
    if check_guest_status(domobj):
        pass
    else:
        domobj.create()
        time.sleep(90)

    old_info = domobj.blockInfo(diskpath, 0)

    try:
        tmp_disksize = disksize * (1 + 1023 * (1 - flag))
        logger.info("resize domain disk to %s" % tmp_disksize)
        domobj.blockResize(diskpath, disksize, flag)

        # Currently, the units of disksize which get from blockInfo is byte.
        block_info = domobj.blockInfo(diskpath, 0)

        if block_info[0] == tmp_disksize:
            logger.info("domain disk resize success")
        else:
            logger.error("error: domain disk change into %s" % block_info[0])
            return 1

    except libvirtError as e:
        if "this feature or command is not currently supported" in e.get_error_message():
            if old_info[0] > tmp_disksize:
                logger.info("Shrink test : disk size is %s, resize to %s."
                            % (old_info[0], tmp_disksize))
                logger.info("Expect result : %s" % e.get_error_message())
                return 0
        else:
            logger.error("API error message: %s, error code is %s"
                         % (e.get_error_message(), e.get_error_code()))
            return 1

    return 0
