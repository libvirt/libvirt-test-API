#!/usr/bin/env python

import os
import math

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import utils

required_params = ('guestname', 'flags',)
optional_params = {}

def check_guest_status(*args):
    """Check guest current status"""
    (domobj, logger) = args
    state = domobj.info()[0]
    logger.debug("current guest status: %s" % state)

    if state == libvirt.VIR_DOMAIN_SHUTOFF or \
       state == libvirt.VIR_DOMAIN_SHUTDOWN or \
       state == libvirt.VIR_DOMAIN_BLOCKED:
        return False
    else:
        return True

def check_savefile_create(*args):
    """Check guest's managed save file be created"""

    (guestname) = args
    cmds = "ls /var/lib/libvirt/qemu/save/%s" % guestname + ".save -lh"
    logger.info("Execute cmd  %s" % cmds)
    (status, output) = utils.exec_cmd(cmds, shell=True)
    if status != 0:
        logger.error("No managed save file")
        return False
    else :
        logger.info("managed save file exists")
        return True

def compare_cachedfile(cachebefore, cacheafter):
    """Compare cached value before managed save and its value after
    managed save """

    diff = cacheafter - cachebefore
    logger.info("diff is %s " % diff)
    percent = math.fabs(diff)/cachebefore
    logger.info("diff percent is %s " % percent)
    if percent < 0.05:
        return True
    else:
        return False

def get_cachevalue():
    """Get the file system cached value """

    cmds = "head -n4 /proc/meminfo|grep Cached|awk '{print $2}'"
    (status, output) = utils.exec_cmd(cmds, shell=True)
    if status != 0:
        logger.error("Fail to run cmd line to get cache")
        return 1
    else:
        logger.debug(output[0])
    cachevalue= int(output[0])
    return cachevalue

def managedsave(params):
    """Managed save a running domain"""

    global logger
    logger = params['logger']
    guestname = params['guestname']
    flags = params ['flags']
    #Save given flags to sharedmod.data
    sharedmod.data['flagsave'] = flags

    logger.info("The given flags are %s " % flags)
    if not '|' in flags:
        flagn = int(flags)
    else:
        # bitwise-OR of flags of managedsave
        flaglist = flags.split('|')
        flagn = 0
        for flag in flaglist:
            flagn |= int(flag)

    conn = sharedmod.libvirtobj['conn']
    domobj = conn.lookupByName(guestname)

    if not check_guest_status(domobj, logger):
        logger.error("Current guest status is shutoff")
        return 1

    try:

        logger.info("bitwise OR value of flags is %s" % flagn)

        if flagn == 0:
            logger.info("managedsave %s domain with no flag" % guestname)
        elif flagn == 1:
            logger.info("managedsave %s domain --bypass-cache" % guestname)
        elif flagn == 2:
            logger.info("managedsave %s domain --running" % guestname)
        elif flagn == 3:
            logger.info("managedsave %s domain --running --bypass-cache"\
                         % guestname)
        elif flagn == 4:
            logger.info("managedsave %s domain --paused" % guestname)
        elif flagn == 5:
            logger.info("managedsave %s domain --paused --bypass-cache"\
                         % guestname)
        elif flagn == 6:
            logger.error("--running and --paused are mutually exclusive")
            return 1
        elif flagn == 7:
            logger.error("--running and --paused are mutually exclusive")
            return 1
        else:
            logger.error("Wrong flags be given and fail to managedsave domain")
            return 1

        #If given flags include bypass-cache,check if bypass file system cache
        if flagn % 2 == 1:
            logger.info("Given flags include --bypass-cache")
            os.system('echo 3 > /proc/sys/vm/drop_caches')
            cache_before = get_cachevalue()
            logger.info("Cached value before managedsave is %s" % cache_before)

            domobj.managedSave(flagn)

            cache_after = get_cachevalue()
            logger.info("Cached value after managedsave is %s" % cache_after)

            if compare_cachedfile(cache_before, cache_after):
                logger.info("Bypass file system cache successfully")
            else:
                logger.error("Bypass file system cache failed")
                return 1
        else:
            domobj.managedSave(flagn)

        #Check if domain has managedsave image
        if  domobj.hasManagedSaveImage(0) and \
            domobj.info()[0]==libvirt.VIR_DOMAIN_SHUTOFF and \
            check_savefile_create(guestname):
            logger.info("Domain %s managedsave successfully " % guestname)
        else:
            logger.error("Fail to managedsave domain")
            return 1

    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % e.message)
        logger.error("Fail to managedsave %s domain" % guestname)
        return 1

    return 0
