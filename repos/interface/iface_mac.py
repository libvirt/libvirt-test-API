#!/usr/bin/env python

import os
import sys
import re
import commands

required_params = ()
optional_params = ('ifacename',)

VIRSH_QUIET_IFACE_LIST = "virsh --quiet iface-list --all | awk '{print ""$%s""}'"
GET_MAC = "ip link show %s |sed -n '2p'| awk '{print $2}'"
VIRSH_IFACE_MAC = "virsh iface-mac %s"

def get_output(command, logger):
    """execute shell command
    """
    status, ret = commands.getstatusoutput(command)
    if status:
        logger.error("executing "+ "\"" +  command  + "\"" + " failed")
        logger.error(ret)
    return status, ret

def get_name_list(params):
    """return mac we need to test
    """
    logger = params['logger']
    name_list=[]

    if 'ifacename' in params:
        ifacename = params['ifacename']
        name_list.append(ifacename)
    else:
        status, ret = get_output(VIRSH_QUIET_IFACE_LIST % 1, logger)
        if not status:
            name_list = ret.split('\n')
        else:
            return 1, name_list

    logger.info("list of mac we are going to test: %s" % name_list)
    return 0, name_list

def iface_mac(params):
    """ test iface_mac, if optional option 'ifacename' is given
        test it, otherwise test all interface name from the output of
        iface-list
    """
    logger = params['logger']
    status, name_list = get_name_list(params)

    if status:
        return 1

    for name in name_list:
        status, mac_str = get_output(VIRSH_IFACE_MAC % name, logger)
        if not status:
            interface_mac = mac_str.rstrip()
            logger.info("the interface mac generated from " \
                        + VIRSH_IFACE_MAC % name + " is: '%s'" % interface_mac)
        else:
            return 1

        status, mac = get_output(GET_MAC % name, logger)
        logger.info("the interace %s's mac from ip link is address: '%s'" % \
                   (name, mac))

        if not status:
            if interface_mac == mac:
                logger.info("the mac from virsh iface-name \n\
                            is equal to what it should be '%s'" % mac)
            else:
                logger.error("the mac '%s'from virsh iface-name \n\
                            is not equal to what it should be '%s'" % mac)
                return 1
    return 0
