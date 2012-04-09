#!/usr/bin/evn python
# To test domain scheduler parameters

import os
import sys
import time
import commands

import libvirt

from utils import utils

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_guest_status(domobj):
    """Check guest current status"""
    state = domobj.info()[0]
    if state == libvirt.VIR_DOMAIN_SHUTOFF or state == libvirt.VIR_DOMAIN_SHUTDOWN:
        domobj.create()
        time.sleep(30)
    # Add check function
        return True
    else:
        return True

def check_sched_params(*args):
    """Check scheduler parameters validity after setting"""
    hypervisor, dicts, guestname, domobj = args
    sched_dict = {}
    if hypervisor == "xen":
        sched_dict = eval(commands.getoutput('xm sched-credit -d %s'
                          % guestname))
        if sched_dict['weight'] == dicts['weight'] and \
          sched_dict['cap'] == dicts['cap']:
            return 0
        else:
            return 1
    if hypervisor == "kvm":
        sched_dict = domobj.schedulerParameters()
        if sched_dict['cpu_shares'] == dicts['cpu_shares']:
            return 0
        else:
            return 1

def sched_params(params):
    """Setting scheduler parameters, argument params is a
       dictionary data type.which includes 'weight' and 'cap'
       keys, by assigning different value to 'weight' and 'cap'
       to verify validity of the result
    """
    uri = params['uri']
    hypervisor = utils.get_hypervisor()
    usage(params, hypervisor)

    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    conn = libvirt.open(uri)
    domobj = conn.lookupByName(guestname)

    if check_guest_status(domobj):
        sched_params = domobj.schedulerParameters()
        logger.info("original scheduler parameters: %s\n" % sched_params)

    if 'xen' in hypervisor:
        str_weight = params['weight']
        str_cap = params['cap']
        for wgt in eval(str_weight):
            for cap in eval(str_cap):
                dicts = {'weight': wgt, 'cap': cap}
                logger.info("setting scheduler parameters: %s" % dicts)
                domobj.setSchedulerParameters(dicts)
                sched_params = domobj.schedulerParameters()
                logger.info("current scheduler parameters: %s\n" % sched_params)

                retval = check_sched_params(hypervisor, dicts,
                                            guestname, domobj)
                if retval == 0:
                    test_result = True
                else:
                    test_result = False
    elif 'kvm' in hypervisor:
        cpu_shares = int(params['cpushares'])
        dicts = {'cpu_shares': cpu_shares}
        logger.info("setting scheduler parameters: %s" % dicts)
        domobj.setSchedulerParameters(dicts)
        sched_params = domobj.schedulerParameters()
        logger.info("current scheduler parameters: %s\n" % sched_params)
        retval = check_sched_params(hypervisor, dicts,
                                    guestname, domobj)
        if retval == 0:
            test_result = True
        else:
            test_result = False
    else:
        logger.error("unsupported hypervisor type: %s" % hypervisor)
        return return_close(conn, logger, 1)

    if test_result:
        return return_close(conn, logger, 0)
    else:
        return return_close(conn, logger, 1)
