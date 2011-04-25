#!/usr/bin/env python
"""testing "virsh list" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Mon Jan 17, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['domain_list', 'get_option_list','check_default_option',
           'check_inactive_option', 'check_all_option']

import os
import sys
import re
import commands

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))


CONFIG_DIR = '/etc/libvirt/qemu'
RUNNING_DIR = '/var/run/libvirt/qemu'
VIRSH_QUIET_LIST = "virsh --quiet list %s|awk '{print $2}'"
VIRSH_LIST = "virsh list %s"


def get_option_list(params):
    """return options we need to test
    """
    logger = params['logger']
    option_list=[]

    if 'listopt' not in params:
        logger.error("option listopt is required")
        return 1, option_list
    else:
        value = params['listopt']

    if value == 'all':
        option_list = [' ', '--all', '--inactive']
    elif value == '--all' or value == '--inactive':
        option_list.append(value)
    else:
        logger.error("value %s is not supported" % value)
        return 1, option_list

    return 0, option_list

def check_all_option(logger):
    """check the output of virsh list with --all option
    """
    entries = os.listdir(CONFIG_DIR)
    logger.debug("%s in %s" % (entries, CONFIG_DIR))
    status, ret = commands.getstatusoutput(VIRSH_QUIET_LIST % '--all')
    if status:
        logger.error("executing "+ "\"" +  VIRSH_QUIET_LIST % "--all" + "\"" \
                     + " failed")
        logger.error(ret)
        return 1

    for entry in entries:
        if not entry.endswith('.xml'):
            continue
        else:
            guest = entry[:-4]
            if guest not in ret:
                logger.error("guest %s not in the output of virsh list" % guest)
                return 1
    return 0

def check_inactive_option(logger):
    """check the output of virsh list with --inactive option
    """
    entries = os.listdir(CONFIG_DIR)
    logger.debug("%s in %s" % (entries, CONFIG_DIR))

    running_dir_entries = os.listdir(RUNNING_DIR)
    logger.debug("%s in %s" % (running_dir_entries, RUNNING_DIR))

    status, ret = commands.getstatusoutput(VIRSH_QUIET_LIST % '--inactive')
    if status:
        logger.error("executing "+ "\"" +  VIRSH_QUIET_LIST % "--inactive" + "\"" \
                     + " failed")
        logger.error(ret)
        return 1

    inactive_guest = []

    for entry in entries:
        if not entry.endswith('.xml'):
            continue
        else:
            if entry in running_dir_entries:
                continue
            else:
                guest = entry[:-4]
                inactive_guest.append(guest)

    inactive_output = ret.split('\n')
    if inactive_output[0] == '':
        inactive_output = []

    if sorted(inactive_guest) != sorted(inactive_output):
        logger.error("virsh list --inactive error")
        return 1

    return 0

def check_default_option(logger):
    """check the output of virsh list"""
    running_dir_entries = os.listdir(RUNNING_DIR)
    logger.debug("%s in %s" % (running_dir_entries, RUNNING_DIR))
    status, ret = commands.getstatusoutput(VIRSH_QUIET_LIST % '')
    if status:
        logger.error("executing "+ "\"" +  VIRSH_QUIET_LIST % " " + "\"" \
                     + " failed")
        logger.error(ret)
        return 1

    running_guest = []
    for entry in running_dir_entries:
        if not entry.endswith('.xml'):
            continue
        else:
            guest = entry[:-4]
            running_guest.append(guest)

    active_output = ret.split('\n')
    if active_output[0] == '':
        active_output = []

    if sorted(running_guest) != sorted(active_output):
        logger.error("virsh list error")
        return 1

    return 0

def execute_virsh_list(logger, option):
    """execute virsh list command with appropriate option given
    """
    status, ret = commands.getstatusoutput(VIRSH_LIST % option)
    if status:
        logger.error("executing " + "\"" + VIRSH_LIST % option + "\"" \
                     + " failed")
        logger.error(ret)
        return 1

    logger.info(ret)

def domain_list(params):
    """test list command to virsh with default, --all, --inactive
    """
    logger = params['logger']
    ret, option_list = get_option_list(params)

    if ret:
        return 1

    for option in option_list:
        if option == ' ':
            logger.info("check the output of virsh list")
            if not check_default_option(logger):
                logger.info("virsh list checking succeeded")
                execute_virsh_list(logger, option)
            else:
                logger.error("virsh list checking failed")
                return 1
        elif option == '--inactive':
            logger.info("check the output of virsh list --inactive")
            if not check_inactive_option(logger):
                logger.info("virsh list --inactive checking succeeded")
                execute_virsh_list(logger, option)
            else:
                logger.error("virsh list --inactive checking failed")
                return 1
        elif option == '--all':
            logger.info("check the output of virsh list --all")
            if not check_all_option(logger):
                logger.info("virsh list --all checking succeeded")
                execute_virsh_list(logger, option)
            else:
                logger.error("virsh list --all checking failed")
                return 1

    return 0
