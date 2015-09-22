#!/usr/bin/env python

import libvirt
from libvirt import libvirtError
import lxml
import lxml.etree

required_params = ()
optional_params = {'conn': '', 'flags': ''}

HOST_HUGEPAGE = '/sys/devices/system/node/node%d/hugepages/hugepages-%dkB/nr_hugepages'

def get_host_pagesize(conn):
    ret = []
    tree = lxml.etree.fromstring(conn.getCapabilities())

    set = tree.xpath("/capabilities/host/cpu/pages")
    for n in set:
        ret.append(int(n.attrib['size']))

    return ret

def get_host_pagecount(pagesize):
    try:
        return int(open(HOST_HUGEPAGE % (0, pagesize)).read())
    except IOError:
        return -1

def connection_allocPages(params):
    """
       test API for allocPages in class virConnect
    """
    logger = params['logger']
    fail=0

    if 'flags' in params:
        if params['flags'] == 'pageset':
            flags = libvirt.VIR_NODE_ALLOC_PAGES_SET
        else:
            logger.error("Unknown flags name: %s" % params['flags'])
            return 1
    else:
        flags = 0

    try:
        if 'conn' in params:
            conn=libvirt.open(params['conn'])
        else:
            conn=libvirt.open(optional_params['conn'])
        logger.info("get connection to libvirtd")
        list1 = get_host_pagesize(conn)

    except libvirtError, e:
        logger.error("API error message: %s" % e.message)
        return 1

    for i in list1:
        logger.info("test hugepage size %d" % i)

        if get_host_pagecount(i) == -1:
            logger.info("Skip system page size %d" % i)
            continue

        try:
            cur_count = get_host_pagecount(i)
            if flags == libvirt.VIR_NODE_ALLOC_PAGES_SET:
                conn.allocPages({i : cur_count + 1}, 0, 1, flags)
            else:
                conn.allocPages({i : 1}, 0, 1, flags)
            if get_host_pagecount(i) != cur_count + 1:
                logger.error("libvirt set a wrong page count to %dKiB hugepage" % i)
                fail = 1
        except libvirtError, e:
            if "Allocated only" in e.message:
                tmp_count = int(e.message.split()[-1])

                if tmp_count != get_host_pagecount(i):
                    logger.error("libvirt output %dKiB hugepage count is not right" % i)
                    fail = 1
            else:
                logger.error("API error message: %s" % e.message)
                return 1

    return fail
