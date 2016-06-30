#!/usr/bin/env python
# Test domain memory peek

import libvirt
from libvirt import libvirtError

from src import sharedmod

required_params = ('guestname', )
optional_params = {}


def memory_peek(params):
    """domain memory peek
    """
    logger = params['logger']
    guestname = params['guestname']

    flag_dict = {'1': "VIR_MEMORY_VIRTUAL", '2': "VIR_MEMORY_PHYSICAL"}

    logger.info("the name of virtual machine is %s" % guestname)

    conn = sharedmod.libvirtobj['conn']

    try:
        domobj = conn.lookupByName(guestname)
        logger.info("test memory peek API")
        for flag in flag_dict.keys():
            logger.info("using flag: %s" % flag_dict[flag])
            mem = domobj.memoryPeek(0, 0, int(flag))
            if mem:
                return 1
            logger.info("memory peek API works fine with flag: %s" %
                        flag_dict[flag])

        logger.info("peek 8 bytes from domain memory")
        for flag in flag_dict.keys():
            logger.info("using flag: %s" % flag_dict[flag])
            mem = domobj.memoryPeek(0, 8, int(flag))
            if not mem:
                return 1
            logger.info("8 bytes start with 0 with flag %s is: %s" %
                        (flag_dict[flag], mem))

    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    return 0
