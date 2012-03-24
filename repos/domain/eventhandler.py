#!/usr/bin/env python
""" To test domain event handler feature through operating a certain
    guest then, do the checking.
    domain:eventhandler
        guestname
            xxx
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Mon Aug 29, 2011'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2011 Red Hat, Inc.'
__all__ = ['eventhandler', 'lifecycle_callback', 'loop_start',
           'loop_stop', 'shutdown_event', 'bootup_event',
           'suspend_event', 'resume_event']

import os
import re
import sys
import time
import threading

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib import connectAPI
from lib import eventAPI
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

LoopThread = None
looping = True
STATE = None

def eventToString(event):
    eventStrings = ( "Defined",
                     "Undefined",
                     "Started",
                     "Suspended",
                     "Resumed",
                     "Stopped",
                     "Shutdown" );
    return eventStrings[event];

def detailToString(event, detail):
    eventStrings = (
        ( "Added", "Updated" ),
        ( "Removed", ),
        ( "Booted", "Migrated", "Restored", "Snapshot" ),
        ( "Paused", "Migrated", "IOError", "Watchdog" ),
        ( "Unpaused", "Migrated"),
        ( "Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot"),
        ( "Finished", )
        )
    return eventStrings[event][detail]

def check_params(params):
    """check out the arguments requried for testing"""
    logger = params['logger']
    keys = ['guestname']
    for key in keys:
        if key not in params:
            logger.error("Argument %s is required" % key)
            return 1
    return 0

def check_domain_running(domobj, guestname, logger):
    """ check if the domain exists, may or may not be active """
    guest_names = domobj.get_list()

    if guestname not in guest_names:
        logger.error("%s doesn't exist or not running" % guestname)
        return 1
    else:
        return 0

def loop_run(eventobj):
    global looping
    while looping:
        eventobj.run_default_impl()

    return 0

def loop_stop(conn):
    """stop event thread and deregister domain callback function"""
    global looping
    global LoopThread
    looping = False
    conn.domain_event_deregister(lifecycle_callback)
    LoopThread.join()

def loop_start(eventobj):
    """start running default event handler implementation"""
    global LoopThread
    eventobj.register_default_impl()
    loop_run_arg = (eventobj,)
    LoopThread = threading.Thread(target=loop_run, args=loop_run_arg, name="libvirtEventLoop")
    LoopThread.setDaemon(True)
    LoopThread.start()

def lifecycle_callback(conn, domain, event, detail, opaque):
    """domain lifecycle callback function"""
    global STATE
    logger = opaque
    logger.debug("lifecycle_callback EVENT: Domain %s(%s) %s %s" % (domain.name(), domain.ID(),
                                                             eventToString(event),
                                                             detailToString(event, detail)))
    STATE = eventToString(event)

def shutdown_event(domobj, guestname, timeout, logger):
    """shutdown the guest, then check the event infomation"""
    global STATE
    STATE = None
    logger.info("power off %s" % guestname)
    try:
        domobj.shutdown(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to power off %s" % guestname)
        return 1

    while timeout:
        if STATE == "Stopped":
            logger.info("The event is Stopped, PASS")
            break
        elif STATE != None:
            logger.error("The event is %s, FAIL", STATE)
            break
        else:
            timeout -= 5
            time.sleep(5)

    if timeout <= 0:
        logger.error("Timeout! The event is %s" % STATE)
        return 1

    return 0

def bootup_event(domobj, guestname, timeout, logger):
    """bootup the guest, then check the event infomation"""
    global STATE
    STATE = None
    logger.info("boot up guest %s" % guestname)
    try:
        domobj.start(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to bootup %s " % guestname)
        return 1

    while timeout:
        if STATE == "Started":
            logger.info("The event is Started, PASS")
            break
        elif STATE != None:
            logger.error("The event is %s, FAIL", STATE)
            break
        else:
            timeout -= 5
            time.sleep(5)

    if timeout <= 0:
        logger.error("Timeout! The event is %s" % STATE)
        return 1

    return 0

def suspend_event(domobj, guestname, timeout, logger):
    """suspend the guest, then check the event infomation"""
    global STATE
    STATE = None
    logger.info("suspend guest %s" % guestname)
    try:
        domobj.suspend(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to suspend %s" % guestname)
        return 1

    while timeout:
        if STATE == "Suspended":
            logger.info("The event is Suspended, PASS")
            break
        elif STATE != None:
            logger.error("The event is %s, FAIL", STATE)
            break
        else:
            timeout -= 5
            time.sleep(5)

    if timeout <= 0:
        logger.error("Timeout! The event is %s" % STATE)
        return 1

    return 0

def resume_event(domobj, guestname, timeout, logger):
    """resume the guest, then check the event infomation"""
    global STATE
    STATE = None
    logger.info("resume guest %s" % guestname)
    try:
        domobj.resume(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to resume %s" % guestname)
        return 1

    while timeout:
        if STATE == "Resumed":
            logger.info("The event is Resumed, PASS")
            break
        elif STATE != None:
            logger.error("The event is %s, FAIL", STATE)
            break
        else:
            timeout -= 5
            time.sleep(5)

    if timeout <= 0:
        logger.error("Timeout! The event is %s" % STATE)
        return 1

    return 0

def eventhandler(params):
    """ perform basic operation for a domain, then checking the result
        by using domain event handler.
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']
    logger.info("the guestname is %s" % guestname)

    eventobj = eventAPI.EventAPI()
    loop_start(eventobj)

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = params['uri']
    conn = connectAPI.ConnectAPI()

    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)

    if check_domain_running(domobj, guestname, logger):
        conn.close()
        return 1

    conn.domain_event_register(lifecycle_callback, logger)

    timeout = 600
    if shutdown_event(domobj, guestname, timeout, logger):
        logger.warn("shutdown_event error")

    if bootup_event(domobj, guestname, timeout, logger):
        logger.warn("bootup_event error")

    if suspend_event(domobj, guestname, timeout, logger):
        logger.warn("suspend_event error")

    if resume_event(domobj, guestname, timeout, logger):
        logger.warn("resume_event error")

    loop_stop(conn)
    conn.close()
    return 0

def eventhandler_clean(params):
    """cleanup the testing environment"""
    pass
