#!/usr/bin/env python
# To test RHBZ 672226

import os
import sys
import re
import commands
import shutil
import urllib
import getpass
from threading import Thread

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import env_parser
from utils import xmlbuilder

IMAG_PATH = "/var/lib/libvirt/images/"
DISK_DD = "dd if=/dev/zero of=%s bs=1 count=1 seek=6G"

required_params = ('guestos', 'guestarch', 'guesttype', 'guestnum')
optional_params = ()

def request_credentials(credentials, user_data):
    for credential in credentials:
        if credential[0] == libvirt.VIR_CRED_AUTHNAME:
            # prompt the user to input a authname. display the provided message
            credential[4] = "root"

            # if the user just hits enter raw_input() returns an empty string.
            # in this case return the default result through the last item of
            # the list
            if len(credential[4]) == 0:
                credential[4] = credential[3]
        elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
            # use the getpass module to prompt the user to input a password.
            # display the provided message and return the result through the
            # last item of the list
            credential[4] = "redhat"
        else:
            return -1

    return 0


class guest_install(Thread):
    """function callable by as a thread to create guest
    """
    def __init__(self, name, os, arch, type, ks, conn, util, logger):
        Thread.__init__(self)
        self.name = name
        self.os = os
        self.arch = arch
        self.type = type
        self.ks = ks
        self.conn = conn
        self.util = util
        self.logger = logger

    def run(self):
        guest_params = {};
        guest_params['guesttype'] = self.type
        guest_params['guestname'] = self.name
        guest_params['kickstart'] = self.ks
        macaddr = self.utils.get_rand_mac()
        guest_params['macaddr'] = macaddr

	# prepare disk image file
        imagepath = IMAG_PATH + self.name
        (status, message) = commands.getstatusoutput(DISK_DD % imagepath)
        if status != 0:
            self.logger.debug(message)
        else:
            self.logger.info("creating disk images file is successful.")

        xmlobj = xmlbuilder.XmlBuilder()
        guestxml = xmlobj.build_domain_install(guest_params)
        self.logger.debug("guestxml is %s" % guestxml)
        self.logger.info('create guest %sfrom xml description' % self.name)
        try:
            guestobj = self.conn.createXML(guestxml, 0)
            self.logger.info('guest %s API createXML returned successfuly' % guestobj.name())
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            self.logger.error("fail to define domain %s" % guestname)
            return 1

        return 0

def multiple_thread_block_on_domain_create(params):
    """ spawn multiple threads to create guest simultaneously
        check the return status of calling create API
    """
    logger = params['logger']
    guestos = params.get('guestos')
    arch = params.get('guestarch')
    type = params.get('guesttype')
    num = params.get('guestnum')

    logger.info("the os of guest is %s" % guestos)
    logger.info("the arch of guest is %s" % arch)
    logger.info("the type of guest is %s" % type)
    logger.info("the number of guest we are going to install is %s" % num)

    hypervisor = utils.get_hypervisor()
    uri = params['uri']

    auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE], request_credentials, None]

    conn = libvirt.openAuth(uri, auth, 0)

    logger.info("the type of hypervisor is %s" % hypervisor)
    logger.debug("the uri to connect is %s" % uri)

    envfile = os.path.join(homepath, 'env.cfg')
    envparser = env_parser.Envpaser(envfile)
    ostree = envparser.get_value("guest", guestos + "_" + arch)
    ks = envparser.get_value("guest", guestos + "_" + arch +
                                "_http_ks")

    # download vmlinuz and initrd.img
    vmlinuzpath = os.path.join(ostree, 'isolinux/vmlinuz')
    initrdpath = os.path.join(ostree, 'isolinux/initrd.img')

    urllib.urlretrieve(vmlinuzpath, '/var/lib/libvirt/boot/vmlinuz')
    urllib.urlretrieve(initrdpath, '/var/lib/libvirt/boot/initrd.img')


    name = "guest"
    start_num = num.split('-')[0]
    end_num = num.split('-')[1]
    thread_pid = []
    for i in range(int(start_num), int(end_num)):
        guestname =  name + str(i)
        thr = guest_install(guestname, guestos, arch, type, ks, conn, util, logger)
        thread_pid.append(thr)

    for id in thread_pid:
        id.start()

    for id in thread_pid:
        id.join()

    conn.close()
    return 0














