#!/usr/bin/evn python
"""This test case is used for testing
   define domain from xml
   mandatory arguments:guesttype
                       guestname
   optional arguments: uuid
                       memory
                       vcpu
                       disksize
                       fullimagepath
                       imagetype
                       hdmodel
                       nicmodel
                       macaddr
                       ifacetype
                       source
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Mon Jan 28, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_define_domain', 'define']

import os
import re
import sys
import commands
import string
import pexpect

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
from lib import domainAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

SSH_KEYGEN = "ssh-keygen -t rsa"
SSH_COPY_ID = "ssh-copy-id"

def usage():
    print '''usage: mandatory arguments:guesttype
                           guestname
       optional arguments: uuid
                           memory
                           vcpu
                           disksize
                           fullimagepath
                           imagetype
                           hdmodel
                           nicmode
                           macaddr
                           ifacetype
                           source
                           target_machine
                           username
                           password
          '''

def check_params(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'guesttype']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            usage()
            return 1
    return 0

def ssh_keygen(logger):
    """using pexpect to generate RSA"""
    logger.info("generate ssh RSA \"%s\"" % SSH_KEYGEN)
    child = pexpect.spawn(SSH_KEYGEN)
    while True:
        index = child.expect(['Enter file in which to save the key ',
                              'Enter passphrase ',
                              'Enter same passphrase again: ',
                               pexpect.EOF,
                               pexpect.TIMEOUT])
        if index == 0:
            child.sendline("\r")
        elif index == 1:
            child.sendline("\r")
        elif index == 2:
            child.sendline("\r")
        elif index == 3:
            logger.debug(string.strip(child.before))
            child.close()
            return 0
        elif index == 4:
            logger.error("ssh_keygen timeout")
            logger.debug(string.strip(child.before))
            child.close()
            return 1

    return 0

def ssh_tunnel(hostname, username, password, logger):
    """setup a tunnel to a give host"""
    logger.info("setup ssh tunnel with host %s" % hostname)
    user_host = "%s@%s" % (username, hostname)
    child = pexpect.spawn(SSH_COPY_ID, [ user_host])
    while True:
        index = child.expect(['yes\/no', 'password: ',
                               pexpect.EOF,
                               pexpect.TIMEOUT])
        if index == 0:
            child.sendline("yes")
        elif index == 1:
            child.sendline(password)
        elif index == 2:
            logger.debug(string.strip(child.before))
            child.close()
            return 0
        elif index == 3:
            logger.error("setup tunnel timeout")
            logger.debug(string.strip(child.before))
            child.close()
            return 1

    return 0

def check_define_domain(guestname, guesttype, target_machine, username, \
                        password, util, logger):
    """Check define domain result, if define domain is successful,
       guestname.xml will exist under /etc/libvirt/qemu/
       and can use virt-xml-validate tool to check the file validity
    """
    if "kvm" in guesttype:
        path = "/etc/libvirt/qemu/%s.xml" % guestname
    elif "xen" in guesttype:
        path = "/etc/xen/%s" % guestname
    else:
        logger.error("unknown guest type")

    if target_machine:
        cmd = "ls %s" % path
        ret, output = util.remote_exec_pexpect(target_machine, username, \
                                               password, cmd)
        if ret:
            logger.error("guest %s xml file doesn't exsits" % guestname)
            return False
        else:
            return True
    else:
        if os.access(path, os.R_OK):
            return True
        else:
            return False

def define(params):
    """Define a domain from xml"""
    # Initiate and check parameters
    params_check_result = check_params(params)
    if params_check_result:
        return 1
    logger = params['logger']
    guestname = params['guestname']
    guesttype = params['guesttype']
    test_result = False

    if params.has_key('target_machine'):
        logger.info("define domain on remote host")
        target_machine = params['target_machine']
        username = params['username']
        password = params['password']
    else:
        logger.info("define domain on local host")
        target_machine = None
        username = None
        password = None

    # Connect to hypervisor connection URI
    util = utils.Utils()
    if target_machine:
        uri = util.get_uri(target_machine)

        #generate ssh key pair
        ret = ssh_keygen(logger)
        if ret:
            logger.error("failed to generate RSA key")
            return 1
        #setup ssh tunnel with target machine
        ret = ssh_tunnel(target_machine, username, password, logger)
        if ret:
            logger.error("faild to setup ssh tunnel with target machine %s" % \
                          target_machine)
            return 1

        commands.getstatusoutput("ssh-add")

    else:
        uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    # Get capabilities debug info
    caps = conn.get_caps()
    logger.debug(caps)

    # Generate damain xml
    dom_obj = domainAPI.DomainAPI(conn)
    xml_obj = xmlbuilder.XmlBuilder()
    domain = xml_obj.add_domain(params)
    xml_obj.add_disk(params, domain)
    xml_obj.add_interface(params, domain)
    dom_xml = xml_obj.build_domain(domain)
    logger.debug("domain xml:\n%s" %dom_xml)

    # Define domain from xml
    try:
        try:
            dom_obj.define(dom_xml)
            if check_define_domain(guestname, guesttype, target_machine, \
                                   username, password, util, logger):
                logger.info("define a domain form xml is successful")
                test_result = True
            else:
                logger.error("fail to check define domain")
                test_result = False
        except LibvirtAPI, e:
            logger.error("fail to define a domain from xml")
            test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if target_machine:
        REMOVE_SSH = "ssh %s \"rm -rf /root/.ssh/*\"" % (target_machine)
        logger.info("remove ssh key on remote machine")
        status, ret = util.exec_cmd(REMOVE_SSH, shell=True)
        if status:
            logger.error("failed to remove ssh key")

        REMOVE_LOCAL_SSH = "rm -rf /root/.ssh/*"
        logger.info("remove local ssh key")
        status, ret = util.exec_cmd(REMOVE_LOCAL_SSH, shell=True)
        if status:
            logger.error("failed to remove local ssh key")

    if test_result:
        return 0
    else:
        return 1

def define_clean(params):
    """ clean testing environment """
    pass
