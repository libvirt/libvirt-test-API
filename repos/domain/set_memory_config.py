#!/usr/bin/env python
# Test set domain balloon memory with flag VIR_DOMAIN_AFFECT_CONFIG
# or VIR_DOMAIN_VCPU_MAXIMUM, depend on which optional param is
# given.

from xml.dom import minidom

import libvirt
from libvirt import libvirtError

from src import sharedmod

required_params = ('guestname', )
optional_params = {'memory': 1048576,
                   'maxmem': 4194304,
                  }
def get_memory_config(domobj):
    """get domain config current memory and max memory
    """
    try:
        guestxml = domobj.XMLDesc(2)
        logger.debug("domain %s xml is :\n%s" %(domobj.name(), guestxml))
        xml = minidom.parseString(guestxml)

        logger.info("get domain memory info in config xml")
        mem = xml.getElementsByTagName('currentMemory')[0]
        current = int(mem.childNodes[0].data)
        logger.info("current memory in config xml is: %s" % current)

        mem = xml.getElementsByTagName('memory')[0]
        max_memory = int(mem.childNodes[0].data)
        logger.info("max memory in config xml is: %s" % max_memory)

    except libvirtError, e:
        logger.error("libvirt call failed: " + str(e))
        return False

    return current, max_memory

def set_memory_config(params):
    """set domain memory with live flag and check
    """
    global logger
    logger = params['logger']
    guestname = params['guestname']
    memory = params.get('memory', None)
    maxmem = params.get('maxmem', None)

    logger.info("the name of virtual machine is %s" % guestname)
    if memory == None and maxmem == None:
        logger.error("at least one of memory or maxmem should be provided")
        return 1

    conn = sharedmod.libvirtobj['conn']

    try:
        domobj = conn.lookupByName(guestname)
        if memory:
            memory = int(memory)
            flags = libvirt.VIR_DOMAIN_AFFECT_CONFIG
            logger.info("set domain memory as %s with flag: %s" %
                        (memory, flags))
            domobj.setMemoryFlags(memory, flags)
            ret = get_memory_config(domobj)
            if not ret:
                return 1

            if ret[0] == memory:
                logger.info("set current memory succeed")
            else:
                logger.error("set current memory failed")
                return 1

        if maxmem:
            maxmem = int(maxmem)
            flags = libvirt.VIR_DOMAIN_MEM_MAXIMUM
            logger.info("set domain max memory as %s with flag: %s" %
                        (maxmem, flags))
            domobj.setMemoryFlags(maxmem, flags)
            ret = get_memory_config(domobj)
            if not ret:
                return 1

            if ret[1] == maxmem:
                logger.info("set max memory succeed")
            else:
                logger.error("set max memory failed")
                return 1

    except libvirtError, e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    return 0
