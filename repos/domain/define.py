#!/usr/bin/evn python

import os
import re
import sys
import commands
import string
import pexpect

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import utils
from utils import xmlbuilder

required_params = ('guestname', 'virt_type',)
optional_params = ('uuid',
                   'memory',
                   'vcpu',
                   'disksize',
                   'fullimagepath',
                   'imagetype',
                   'hdmodel',
                   'nicmodel',
                   'macaddr',
                   'ifacetype',
                   'source',)

def check_define_domain(guestname, virt_type, hostname, username, \
                        password, util, logger):
    """Check define domain result, if define domain is successful,
       guestname.xml will exist under /etc/libvirt/qemu/
       and can use virt-xml-validate tool to check the file validity
    """
    if "kvm" in virt_type:
        path = "/etc/libvirt/qemu/%s.xml" % guestname
    elif "xen" in virt_type:
        path = "/etc/xen/%s" % guestname
    else:
        logger.error("unknown virt type")

    if hostname:
        cmd = "ls %s" % path
        ret, output = utils.remote_exec_pexpect(hostname, username, \
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
    logger = params['logger']
    guestname = params['guestname']
    virt_type = params['virt_type']
    conn = sharedmod.libvirtobj['conn']
    uri = conn.getURI()

    hostname = utils.parser_uri(uri)[1]

    username = params['username']
    password = params['password']
    logger.info("define domain on %s" % uri)

    # Generate damain xml
    xml_obj = xmlbuilder.XmlBuilder()
    domain = xml_obj.add_domain(params)
    xml_obj.add_disk(params, domain)
    xml_obj.add_interface(params, domain)
    dom_xml = xml_obj.build_domain(domain)
    logger.debug("domain xml:\n%s" %dom_xml)

    # Define domain from xml
    try:
        conn.defineXML(dom_xml)
        if check_define_domain(guestname, virt_type, hostname, \
                               username, password, util, logger):
            logger.info("define a domain form xml is successful")
        else:
            logger.error("fail to check define domain")
            return 1
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    return 0
