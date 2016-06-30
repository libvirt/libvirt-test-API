#!/usr/bin/env python
# volume resize testing with delta flags, libvirt storage
# driver only support dir now

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import utils

required_params = ('poolname', 'volname', 'capacity',)
optional_params = {}


def vol_resize_delta(params):
    """test volume resize with delta flags"""

    global logger
    logger = params['logger']
    poolname = params['poolname']
    volname = params['volname']
    capacity = params['capacity']

    logger.info("the poolname is %s, volname is %s" %
                (poolname, volname))

    logger.info("the capacity given is %s" % capacity)
    out = utils.get_capacity_suffix_size(capacity)
    capacity_val = out['capacity_byte']
    logger.debug("the capacity to byte is %s" % capacity_val)

    conn = sharedmod.libvirtobj['conn']
    try:
        poolobj = conn.storagePoolLookupByName(poolname)
        vol = poolobj.storageVolLookupByName(volname)

        logger.info("get volume info before resize")
        out = vol.info()
        pre_capacity = out[1]
        pre_allocation = out[2]
        logger.info("volume capacity is %s bytes, allocation is %s bytes" %
                    (pre_capacity, pre_allocation))

        flag = libvirt.VIR_STORAGE_VOL_RESIZE_DELTA
        logger.info("resize %s with capacity %s in pool %s using flag: %s"
                    % (volname, capacity, poolname, flag))

        vol.resize(capacity_val, flag)

        logger.info("get volume info after resize")
        out = vol.info()
        post_capacity = out[1]
        post_allocation = out[2]
        logger.info("volume capacity is %s bytes, allocation is %s bytes" %
                    (post_capacity, post_allocation))

        logger.info("check resize effect")
        if post_capacity - pre_capacity == capacity_val:
            logger.info("increased size is expected")
        else:
            logger.error("increase size not equal to set, resize failed")
            return 1

        if pre_allocation == post_allocation:
            logger.info("allocation is expected")
        else:
            logger.error("allocation changed, resize failed")
            return 1

        logger.info("resize succeed")

    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    return 0
