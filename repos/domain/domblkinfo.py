#!/usr/bin/env python
# To test "virsh domblkinfo" command

import os
import sys
import re
import commands

import libvirt
from libvirt import libvirtError

import sharedmod

required_params = ('guestname', 'blockdev',)
optional_params = ()

GET_DOMBLKINFO_MAC = "virsh domblkinfo %s %s | awk '{print $2}'"
GET_CAPACITY = "du -b %s | awk '{print $1}'"
GET_PHYSICAL_K = " du -B K %s | awk '{print $1}'"
VIRSH_DOMBLKINFO = "virsh domblkinfo %s %s"

def get_output(command, logger):
    """execute shell command
    """
    status, ret = commands.getstatusoutput(command)
    if status:
        logger.error("executing "+ "\"" +  command  + "\"" + " failed")
        logger.error(ret)
    return status, ret

def check_domain_exists(conn, guestname, logger):
    """ check if the domain exists, may or may not be active """
    guest_names = []
    ids = conn.listDomainsID()
    for id in ids:
        obj = conn.lookupByID(id)
        guest_names.append(obj.name())

    guest_names += conn.listDefinedDomains()

    if guestname not in guest_names:
        logger.error("%s doesn't exist" % guestname)
        return False
    else:
        return True

def check_block_data(blockdev, blkdata, logger):
    """ check data about capacity,allocation,physical """
    status, apparent_size = get_output(GET_CAPACITY % blockdev, logger)
    if not status:
        if apparent_size == blkdata[0]:
            logger.info("the capacity of '%s' is %s, checking succeeded" % \
                        (blockdev, apparent_size))
        else:
            logger.error("apparent-size from 'du' is %s, \n\
                         but from 'domblkinfo' is %s, checking failed" % \
                        (apparent_size, blkdata[0]))
            return 1
    else:
        return 1

    status, block_size_k = get_output(GET_PHYSICAL_K % blockdev, logger)
    if not status:
        block_size_b = int(block_size_k[:-1]) * 1024
        # Temporarily, we only test the default case, assuming
        # Allocation value is equal to Physical value
        if str(block_size_b) == blkdata[1] and str(block_size_b) == blkdata[2]:
            logger.info("the block size of '%s' is %s, same with \n\
                        Allocation and Physical value, checking succeeded" % \
                         (blockdev, block_size_b))
        else:
            logger.error("the block size from 'du' is %s, \n\
                          the Allocation value is %s, Physical value is %s, \n\
                          checking failed" % (block_size_b, blkdata[1], blkdata[2]))
            return 1

    return 0


def domblkinfo(params):
    """ using du command to check the data
        in the output of virsh domblkinfo
    """
    logger = params['logger']
    guestname = params.get('guestname')
    blockdev = params.get('blockdev')

    logger.info("the name of guest is %s" % guestname)
    logger.info("the block device is %s" % blockdev)

    conn = sharedmod.libvirtobj['conn']

    if not check_domain_exists(conn, guestname, logger):
        logger.error("need a defined guest")
        return 1

    logger.info("the output of virsh domblkinfo is:")
    status, output = get_output(VIRSH_DOMBLKINFO % (guestname, blockdev), logger)
    if not status:
        logger.info("\n" + output)
    else:
        return 1

    status, data_str = get_output(GET_DOMBLKINFO_MAC % (guestname, blockdev), logger)
    if not status:
        blkdata = data_str.rstrip().split('\n')
        logger.info("capacity,allocation,physical list: %s" % blkdata)
    else:
        return 1

    if check_block_data(blockdev, blkdata, logger):
        logger.error("checking domblkinfo data FAILED")
        return 1
    else:
        logger.info("checking domblkinfo data SUCCEEDED")
    return 0
