# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
import operator
import re
import libvirt

from libvirt import libvirtError
from libvirttestapi.utils import utils

SPLIT_STR = " -"

required_params = ('nativeformat', 'guestname')
optional_params = {}


def check_domxml_to_native(nativeconfig, guestname):
    cmd = "cat /var/run/libvirt/qemu/%s.pid" % guestname
    ret, guest_pid = utils.exec_cmd(cmd, shell=True)
    cmd = "cat -v /proc/%s/cmdline" % guest_pid[0]
    ret, guest_cmdline = utils.exec_cmd(cmd, shell=True)
    nativeconLog = re.sub(r'\^@', ' ', guest_cmdline[0]).strip(' ')
    env_params_list = ['LC_ALL', 'PATH', 'XDG_DATA_HOME',
                       'XDG_CACHE_HOME', 'XDG_CONFIG_HOME',
                       'QEMU_AUDIO_DRV', 'HOME']
    for i in env_params_list:
        if i in nativeconfig:
            nativeconfig = re.sub(r'%s.[^\s]+\s' % i, '', nativeconfig)

    nativeconLog = nativeconLog.split(SPLIT_STR)
    nativeconfig = nativeconfig.split(SPLIT_STR)

    # Remove the netdev part because mac is always be zero,
    #
    # Remove vnc port because the port will change if there are
    # other vnc guests on the host, and this is not a problem for
    # this API.
    #
    # Remove 'object' and 'chardev' item because it contains
    # dynamic domain ID.

    #convert native config from log
    temp = nativeconLog[:]
    skipped_item = ['netdev', 'object', 'chardev']
    for item in temp:
        if any([i for i in skipped_item if i in item]):
            nativeconLog.remove(item)

        if "vnc" in item:
            ret = nativeconLog.index(item)
            nativeconLog.remove(item)
            item = item.split(":")[0]
            nativeconLog.insert(ret, item)

        if "S" == item:
            nativeconLog.remove(item)

    #convert native config from API
    temp = nativeconfig[:]
    for item in temp:
        if any([i for i in skipped_item if i in item]):
            nativeconfig.remove(item)

        if "vnc" in item:
            ret = nativeconfig.index(item)
            nativeconfig.remove(item)
            item = item.split(":")[0]
            nativeconfig.insert(ret, item)

        if "S" == item:
            nativeconLog.remove(item)

    nativeconLog = SPLIT_STR.join(nativeconLog)
    nativeconfig = SPLIT_STR.join(nativeconfig)

    logger.debug("Native config from domain log is:  %s" % nativeconLog)
    logger.info("Native config from API is :  %s" % nativeconfig)
    if operator.eq(nativeconLog, nativeconfig):
        logger.info("native config from API can match the config form log")
        return 0
    else:
        logger.error("native config from API is not same with log")
        return 1

    return 0


def domxml_to_native(params):
    """Test API domainXMLFromNative to convert
       a native configuration to a domain XML
       configuration
    """
    global logger
    logger = params['logger']
    conn = libvirt.open()
    nativeformat = params['nativeformat']
    guestname = params['guestname']
    guest = conn.lookupByName(guestname)
    xmlstr = guest.XMLDesc()

    try:
        nativeconfig = conn.domainXMLToNative(nativeformat, xmlstr, 0)
        if check_domxml_to_native(nativeconfig, guestname):
            logger.error("The domain xml get from API domainXMLFromNative is \
                         not right")
            return 1
        else:
            logger.info("The domain xml get from API domainXMLFromNative \
                        successfully!")
            return 0
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        return 1

    return 0
