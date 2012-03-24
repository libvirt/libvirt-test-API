#!/usr/bin/evn python
"""this test case is used for testing domain
   scheduler parameters
   mandatory arguments for xen :guestname
                                weight
                                cap
   mandatory arguments for kvm :guestname
                                cpushares
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu Oct 22, 2009'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_sched_params',
           'sched_params']

import os
import sys
import time
import commands

dir = os.path.dirname(sys.modules[__name__].__file__)
absdir = os.path.abspath(dir)
rootdir = os.path.split(os.path.split(absdir)[0])[0]
sys.path.append(rootdir)

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def usage(params, hypervisor):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    if 'xen' in hypervisor:
        keys = ['guestname', 'weight', 'cap']
    elif 'kvm' in hypervisor:
        keys = ['guestname','cpushares']
    else:
        logger.error("unsupported hypervisor type: %s" % hypervisor)
        return 1
    for key in keys:
        if key not in params:
            logger.error("%s is required" % key)
            return 1

def check_guest_status(guestname, domobj):
    """Check guest current status"""
    state = domobj.get_state(guestname)
    if state == "shutoff" or state == "shutdown":
        domobj.start(guestname)
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
        sched_dict = domobj.get_sched_params(guestname)
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
    util = utils.Utils()
    uri = params['uri']
    hypervisor = util.get_hypervisor()
    usage(params, hypervisor)

    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    domobj = domainAPI.DomainAPI(virconn)
    if check_guest_status(guestname, domobj):
        sched_params = domobj.get_sched_params(guestname)
        logger.info("original scheduler parameters: %s\n" % sched_params)

    if 'xen' in hypervisor:
        str_weight = params['weight']
        str_cap = params['cap']
        for wgt in eval(str_weight):
            for cap in eval(str_cap):
                dicts = {'weight': wgt, 'cap': cap}
                logger.info("setting scheduler parameters: %s" % dicts)
                domobj.set_sched_params(guestname, dicts)
                sched_params = domobj.get_sched_params(guestname)
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
        domobj.set_sched_params(guestname, dicts)
        sched_params = domobj.get_sched_params(guestname)
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
