#!/usr/bin/env python

import os
import sys
import re
import commands

required_params = ('ifaceopt')
optional_params = ()

VIRSH_QUIET_IFACE_LIST = "virsh --quiet iface-list %s | awk '{print ""$%s""}'"
NETWORK_CONFIG = "/etc/sysconfig/network-scripts/"
IFCONFIG_DRIVER = "ifconfig %s | sed 's/[ \t].*//;/^$/d'"
GET_MAC = "ip link show %s |sed -n '2p'| awk '{print $2}'"
VIRSH_IFACE_LIST = "virsh iface-list %s"

names = []
state = []
macs = []

def get_option_list(params):
    """return options we need to test
    """
    logger = params['logger']
    option_list=[]

    value = params['ifaceopt']

    if value == 'all':
        option_list = [' ', '--all', '--inactive']
    elif value == '--all' or value == '--inactive':
        option_list.append(value)
    else:
        logger.error("value %s is not supported" % value)
        return 1, option_list

    return 0, option_list

def get_output(command, logger):
    """execute shell command
    """
    status, ret = commands.getstatusoutput(command)
    if status:
        logger.error("executing "+ "\"" +  command  + "\"" + " failed")
        logger.error(ret)
    return status, ret

def get_interface_list(option, logger):
    """ return active host interface list """
    interface_list = []
    status, interface_str = get_output(IFCONFIG_DRIVER % option, logger)
    if not status:
        interface_list = interface_str.split('\n')
        return interface_list
    else:
        logger.error("\"" + IFCONFIG_DRIVER % option + "\"" + "error")
        logger.error(interface_str)
        return interface_list

def check_ifacename(names, option, logger):
    """ verify the validity of output data """
    ifcfg_files = []
    for f in os.listdir(NETWORK_CONFIG):
        if f.startswith("ifcfg-"):
            f_path = os.path.join(NETWORK_CONFIG, f)
            if os.path.isfile(f_path):
                ifcfg_files.append(f_path)
            else:
                logger.warn("%s is not a regular file" % f_path)

    interface_active = get_interface_list('', logger)
    logger.debug("list of active host interface: %s" % interface_active)
    if interface_active == None:
        return 1

    interface_all = get_interface_list('-a', logger)
    logger.debug("list of all host interface: %s" % interface_all)
    if interface_all == None:
        return 1


    for ifcfg_file in ifcfg_files:
        fp = open(ifcfg_file, 'r')
        fp.seek(0,0)
        for eachLine in fp:
            if eachLine.startswith('DEVICE'):
                device_str = eachLine.rstrip()
                nic_string = device_str.split("=")[1]
                if nic_string.startswith("\""):
                    nic_name = nic_string[1:-1]
                else:
                    nic_name = nic_string
                break

        fp.close()

        if option == ' ':
            if nic_name not in interface_active:
                continue
            else:
                if nic_name in names:
                    logger.info("it contains interface %s in %s" % (nic_name, ifcfg_file))
                else:
                    logger.error("interface %s in %s couldn't \n\
                              be in the output of virsh iface-list with option %s" % \
                              (nic_name, ifcfg_file, option))
                    return 1
        elif option == '--all':
            if nic_name in names:
                logger.info("it contains interface %s in %s" % (nic_name, ifcfg_file))
            else:
                logger.error("interface %s in %s couldn't \n\
                              be in the output of virsh iface-list with option %s" % \
                              (nic_name, ifcfg_file, option))

                return 1
        elif option == '--inactive':
            if nic_name in interface_active:
                continue
            else:
                if nic_name in names:
                    logger.info("it contains interface %s in %s" % (nic_name, ifcfg_file))
                else:
                    logger.error("interface %s in %s couldn't \n\
                              be in the output of virsh iface-list with option %s" % \
                              (nic_name, ifcfg_file, option))
                    return 1

    return 0

def check_ifacestate(names, state, logger):
    """ check the state of give host interface """

    interface_active = get_interface_list('', logger)
    if interface_active == None:
        return 1

    interface_all = get_interface_list('-a', logger)
    if interface_all == None:
        return 1

    index = 0
    count = len(names)
    while(index < count):
        if names[index] in interface_active and state[index] == 'active':
            logger.info("interface %s is %s" % (names[index], state[index]))
        elif names[index] not in interface_active and \
             names[index] in interface_all and \
             state[index] == 'inactive':
            logger.info("interface %s is %s" % (names[index], state[index]))
        else:
            logger.error("interface %s is %s, but not we expected" % \
                        (names[index], state[index]))
            return 1

        index = index + 1

    return 0

def check_ifacemac(names, macs, logger):
    """ check if the mac corresponding to approriate name is correct """
    index = 0
    count = len(names)
    while(index < count):
        status, mac_shell = get_output(GET_MAC % names[index], logger)
        if not status:
            if mac_shell == macs[index]:
                logger.info("interface %s's mac address is %s" % \
                            (names[index], macs[index]))
            else:
                logger.error("interface %s's mac address from iface-list: %s \
                              is different from one from ip link show: %s" % \
                             (name[index], macs[indesx], mac_shell))
                return 1
        index = index + 1

    return 0

def iface_list_output(option, logger):
    """ check the output of virsh iface-list with appropriate option """
    global names, state, macs

    status, ret = get_output(VIRSH_QUIET_IFACE_LIST % (option, 1), logger)
    if not status:
        names = ret.split('\n')
        logger.info("interface names from option '%s' : %s" % (option, names))

    else:
        return 1

    status, ret = get_output(VIRSH_QUIET_IFACE_LIST % (option, 2), logger)
    if not status:
        state = ret.split('\n')
        logger.info("interface state from option '%s' : %s" % (option, state))
    else:
        return 1

    status, ret = get_output(VIRSH_QUIET_IFACE_LIST % (option, 3), logger)
    if not status:
        macs = ret.split('\n')
        logger.info("interface macs from option '%s' : %s" % (option, macs))
    else:
        return 1

    return 0

def iface_list(params):
    """ test the validity of the output of iface_list with
        default, --all, --inactive option, including
        interface name, state, and mac
    """
    logger = params['logger']
    ret, option_list = get_option_list(params)
    global names, state, macs

    if ret:
        return 1

    for option in option_list:
            logger.info("CHECK the output of virsh pool-list with option '%s'" % option)
            logger.info("get the name, corresponding state and mac address of interfaces")
            if iface_list_output(option, logger):
                logger.error("faied to name, state, and mac from iface-list")
                return 1
            else:
                logger.info("then, check the validity of these interface names")
                if check_ifacename(names, option, logger):
                    logger.error("checking interface names FAILED")
                    return 1
                else:
                    logger.info("checking interface names SUCCESSFULLY")

                logger.info("check the state of these interfaces")
                if check_ifacestate(names, state, logger):
                    logger.error("checking interface state FAILED")
                    return 1
                else:
                    logger.info("checking interface state SUCCESSFULLY")

                logger.info("check the interface mac address")
                if check_ifacemac(names, macs, logger):
                    logger.error("checking interface mac address FAILED")
                    return 1
                else:
                    logger.info("checking interface mac address SUCESSFULLY")

                status, ret = get_output(VIRSH_IFACE_LIST % option, logger)
                if not status:
                    logger.info("\n" + ret)

    return 0
