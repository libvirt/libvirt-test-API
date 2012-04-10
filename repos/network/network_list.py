#!/usr/bin/env python
"""testing "virsh net-list" function
"""

import os
import sys
import re
import commands

import libvirt
from libvirt import libvirtError

from utils import utils

VIRSH_QUIET_NETLIST = "virsh --quiet net-list %s|awk '{print $1}'"
VIRSH_NETLIST = "virsh net-list %s"
GET_BRIDGE_IP = "/sbin/ifconfig %s | grep 'inet addr:' | cut -d: -f2 | awk '{print $1}'"
CONFIG_DIR = "/etc/libvirt/qemu/networks/"

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def get_option_list(params):
    """return options we need to test
    """
    logger = params['logger']
    option_list=[]

    if 'netlistopt' not in params:
        logger.error("option listopt is required")
        return 1, option_list
    else:
        value = params['netlistopt']

    if value == 'all':
        option_list = [' ', '--all', '--inactive']
    elif value == '--all' or value == '--inactive':
        option_list.append(value)
    else:
        logger.error("value %s is not supported" % value)
        return 1, option_list

    return 0, option_list

def get_output(logger, command, flag):
    """execute shell command
    """
    status, ret = commands.getstatusoutput(command)
    if not flag and status:
        logger.error("executing "+ "\"" +  command  + "\"" + " failed")
        logger.error(ret)
    return status, ret

def check_all_option(conn, util, logger):
    """check the output of virsh net-list with --all option
    """
    all_network = []
    entries = os.listdir(CONFIG_DIR)
    logger.debug("%s in %s" % (entries, CONFIG_DIR))
    status, network_names = get_output(logger, VIRSH_QUIET_NETLIST % '--all', 0)
    if not status:
        all_network = network_names.split('\n')
        logger.info("all network is %s" % all_network)
    else:
        return 1

    if all_network == ['']:
        return 0

    for entry in entries:
        if not entry.endswith('.xml'):
            continue
        else:
            network = entry[:-4]
            if network not in all_network:
                logger.error("network %s not in the output of virsh net-list" % network)
                return 1
    return 0

def check_inactive_option(conn, util, logger):
    """check the output of virsh net-list with --inactive option
    """
    inactive_network = []
    status, network_names = get_output(logger, VIRSH_QUIET_NETLIST % '--inactive', 0)
    if not status:
        inactive_network = network_names.split('\n')
        logger.info("inactive network: %s" % inactive_network)
    else:
        return 1

    if inactive_network == ['']:
        return 0

    for network in inactive_network:
        try:
            netobj = conn.networkLookupByName(network)
            bridgename = netobj.bridgeName()
            status, ip = get_output(logger, GET_BRIDGE_IP % bridgename, 1)

            if not status:
                logger.info("network %s is inactive as we expected" % network)
            else:
                logger.error("network %s is not inactive, wrong" % network)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1

    return 0

def check_default_option(conn, util, logger):
    """check the output of virsh net-list
    """
    active_network = []
    status, network_names = get_output(logger, VIRSH_QUIET_NETLIST % '', 0)
    if not status:
        active_network = network_names.split('\n')
        logger.info("running network: %s" % active_network)
    else:
        return 1

    if active_network == ['']:
        return 0

    for network in active_network:
        try:
            netobj = conn.networkLookupByName(network)
            bridgename = netobj.bridgeName()
            status, ip = get_output(logger, GET_BRIDGE_IP % bridgename, 0)
            if not status and util.do_ping(ip, 0):
                logger.info("network %s is active as we expected" % network)
                logger.debug("%s has ip: %s" % (bridgename, ip))
            else:
                logger.error("network %s has no ip or fails to ping" % network)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1

    return 0

def execute_virsh_netlist(option, logger):
    """execute virsh net-list command with appropriate option given
    """
    status, ret = get_output(logger, VIRSH_NETLIST % option, 0)
    if not status:
        logger.info(ret)

def network_list(params):
    """test net-list command to virsh with default, --all, --inactive
    """
    logger = params['logger']
    ret, option_list = get_option_list(params)

    if ret:
        return 1

    uri = params['uri']
    conn = libvirt.open(uri)

    for option in option_list:
        if option == ' ':
            logger.info("check the output of virsh net-list")
            if not check_default_option(conn, util, logger):
                logger.info("virsh net-list checking succeeded")
                execute_virsh_netlist(option, logger)
            else:
                logger.error("virsh net-list checking failed")
                return return_close(conn, logger, 1)
        elif option == '--inactive':
            logger.info("check the output of virsh net-list --inactive")
            if not check_inactive_option(conn, util, logger):
                logger.info("virsh net-list --inactive checking succeeded")
                execute_virsh_netlist(option, logger)
            else:
                logger.error("virsh net-list --inactive checking failed")
                return return_close(conn, logger, 1)
        elif option == '--all':
            logger.info("check the output of virsh net-list --all")
            if not check_all_option(conn, util, logger):
                logger.info("virsh net-list --all checking succeeded")
                execute_virsh_netlist(option, logger)
            else:
                logger.error("virsh net-list --all checking failed")
                return return_close(conn, logger, 1)

    return return_close(conn, logger, 0)
