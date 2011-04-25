#!/usr/bin/env python
"""this test case is used for testing dumpping the core of
   a domain on a given file for analysis.
   mandatory arguments: guestname
                        file
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Fri Dec 25, 2009'
__version__ = '0.1.2'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_guest_kernel',
           'check_core_dump', 'core_dump']

import os
import re
import sys
import time
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

from lib.Python import connectAPI
from lib.Python import domainAPI
from utils.Python import utils
from utils.Python import check
from exception import LibvirtAPI

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def usage(dicts):
    """Verify inputing parameter dictsionary"""
    logger = dicts['logger']
    keys = ['guestname', 'file']
    for key in keys:
        if key not in dicts:
            logger.error("%s is required" %key)
            return 1

def check_guest_status(*args):
    """Check guest current status"""
    (guestname, domobj, logger) = args

    state = domobj.get_state(guestname)
    logger.debug("current guest status: %s" %state)
    if state == "shutoff" or state == "shutdown":
        domobj.start(guestname)
        time.sleep(60)
        logger.debug("current guest status: %s" %state)
    # add check function
        return True
    else:
        return True

def check_guest_kernel(*args):
    """Check guest kernel version"""
    (guestname, logger) = args

    util = utils.Utils()
    chk = check.Check()

    mac = util.get_dom_mac_addr(guestname)
    logger.debug("guest mac address: %s" %mac)

    ipaddr = util.mac_to_ip(mac, 15)
    if ipaddr == None:
        logger.error("can't get guest ip")
        return None

    logger.debug("guest ip address: %s" %ipaddr)

    kernel = chk.get_remote_kernel(ipaddr, "root", "redhat")
    logger.debug("current kernel version: %s" %kernel)

    if kernel:
        return kernel
    else:
        return None

def check_core_dump(*args):
    """Check dumpping core file validity"""
    (guestname, file, kernel, logger) = args

    kernel = check_guest_kernel(guestname, logger)
    (big, other) = kernel.split("-")
    small = other.split(".")
    arch = small[-1]
    pkgs  = ["kernel-debuginfo-%s" % (kernel),
             "kernel-debuginfo-common-%s-%s" % (arch, kernel)]

    req_pkgs = ""
    for pkg in pkgs:
        req_pkgs = req_pkgs + pkg + ".rpm "
        status, output = commands.getstatusoutput("rpm -q %s" %pkg)
        down = "wget \
                http://download.devel.redhat.com/brewroot/packages/kernel\
                /%s/%s.%s/%s/%s.rpm" % (big, small[0], small[1], arch, pkg)
        if status != 0:
            logger.info("Please waiting for some time,downloading...")
            stat, ret = commands.getstatusoutput(down)
            if stat != 0:
                logger.error("download failed: %s" %ret)
            else:
                logger.info(ret)
        else:
            logger.debug(output)

    st, res = commands.getstatusoutput("rpm -ivh %s" % req_pkgs )
    if st != 0:
        logger.error("fail to install %s" % req_pkgs)
    else:
        logger.info(res)


    if file:
        cmd = "crash /usr/lib/debug/lib/modules/%s/vmlinux %s" % \
              (kernel, file)
        logger.info("crash cmd line: %s" %cmd)
        status, output = commands.getstatusoutput(cmd)
        if status == 0:
            logger.info("crash executes result: %d" %status)
            return 0
        else:
            logger.info("screen output information: %s" %output)
            return 1
    else:
        logger.debug("file argument is required")
        return 1

def check_core_dump1(*args):
    """check whether core dump file is generated"""
    (core_file_path, logger) = args
    if os.access(core_file_path, os.R_OK):
        logger.info("core dump file path: %s is existing." % core_file_path)
        return 0
    else:
        logger.info("core dump file path: %s is NOT existing!!!" %
                     core_file_path)
        return 1

def core_dump(dicts):
    """This method will dump the core of a domain on a given file
       for analysis. Note that for remote Xen Daemon the file path
       will be interpreted in the remote host.
    """
    # Initiate and check parameters
    usage(dicts)
    logger = dicts['logger']
    guestname = dicts['guestname']
    file = dicts['file']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    # Domain core dump
    domobj = domainAPI.DomainAPI(virconn)

    if check_guest_status(guestname, domobj, logger):
        kernel = check_guest_kernel(guestname, logger)
        if kernel == None:
            logger.error("can't get guest kernel version")
            test_result = False
            return return_close(conn, logger, 1)

        logger.info("dump the core of %s to file %s\n" %(guestname, file))

        try:
            domobj.core_dump(guestname, file)
            retval = check_core_dump1(file, logger)

            if retval == 0:
                test_result = True
                logger.info("check core dump: %d\n" %retval)
            else:
                test_result = False
                logger.error("check core dump: %d\n" %retval)
                return return_close(conn, logger, 1)

        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" % \
                         (e.response()['message'], e.response()['code']))
            logger.error("Error: fail to core dump %s domain" %guestname)
            test_result = False
            return return_close(conn, logger, 1)

    if test_result:
        return return_close(conn, logger, 0)
    else:
        return return_close(conn, logger, 1)

def core_dump_clean(params):
    """ clean testing environment """
    logger = params['logger']
    filepath = params['file']
    if os.path.exists(filepath):
        logger.info("remove dump file from core dump %s" % filepath)
        os.remove(filepath)

