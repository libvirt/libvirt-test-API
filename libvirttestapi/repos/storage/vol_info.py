# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# storage pool volume info

import libvirt

from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.utils.utils import exec_cmd, version_compare, isRelease

required_params = ('poolname', 'volname', 'flags')
optional_params = {}


def check_vol_info(info, vol_path, flags, logger):
    # check capacity
    if isRelease("8", logger) or version_compare("qemu-kvm-rhev", 2, 10, 0, logger):
        cmd = "qemu-img info -U %s | grep 'virtual size' | awk '{print $4}' | sed 's/(//g'" % vol_path
    else:
        cmd = "qemu-img info %s | grep 'virtual size' | awk '{print $4}' | sed 's/(//g'" % vol_path

    ret, out = exec_cmd(cmd, shell=True)
    if ret:
        logger.error("cmd: %s" % cmd)
        logger.error("ret: %s, out: %s" % (ret, out))
        return 1

    if out[0] != str(info[1]):
        return 1

    # check allocation
    if flags == "VIR_STORAGE_VOL_USE_ALLOCATION":
        cmd = "du %s | awk '{print $1}'" % vol_path
    # check physical
    elif flags == "VIR_STORAGE_VOL_GET_PHYSICAL":
        cmd = "ls -al %s | awk '{print $5}'" % vol_path
    ret, out = exec_cmd(cmd, shell=True)
    if ret:
        logger.error("cmd: %s" % cmd)
        logger.error("ret: %s, out: %s" % (ret, out))
        return 1

    if out[0] != str(info[2]):
        return 1

    return 0


def vol_info(params):
    """storage pool volume info testing"""

    logger = params['logger']
    poolname = params['poolname']
    volname = params['volname']
    flags = params['flags']

    if not version_compare("libvirt-python", 3, 0, 0, logger):
        logger.info("Current libvirt-python don't support infoFlags().")
        return 0

    logger.info("poolname: %s" % poolname)
    logger.info("volume name: %s" % volname)
    logger.info("flags: %s" % flags)

    conn = sharedmod.libvirtobj['conn']
    try:
        poolobj = conn.storagePoolLookupByName(poolname)

        logger.info("lookup the volume object by name: %s" % volname)
        volobj = poolobj.storageVolLookupByName(volname)
        if flags == "VIR_STORAGE_VOL_USE_ALLOCATION":
            info = volobj.infoFlags(libvirt.VIR_STORAGE_VOL_USE_ALLOCATION)
        elif flags == "VIR_STORAGE_VOL_GET_PHYSICAL":
            info = volobj.infoFlags(libvirt.VIR_STORAGE_VOL_GET_PHYSICAL)
        else:
            logger.error("Flags %s is not supported." % flags)
            return 1

        logger.info("Info: %s" % info)
        vol_path = volobj.path()
        if check_vol_info(info, vol_path, flags, logger):
            logger.error("Fail to get volume info with flag.")
            return 1

    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    logger.info("Pass to get volume info with flag.")
    return 0
