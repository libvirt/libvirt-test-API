#!/usr/bin/env python
"""Update virtual device to guest from an XML file
   domain:update_devflag
       guestname
           xxx
       devtype
           cdrom|floppy
       username
           xxx
       password
           xxx
"""

import os
import re
import sys
import time
from xml.dom import minidom

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

def check_params(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'devtype', 'username', 'password']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
    return 0

def create_image(params, util, img_name):
    """Create an image file"""
    logger = params['logger']

    if params['devtype'] == 'cdrom':
        cmd1 = "uuidgen|cut -d- -f1"
        ret1, out1 = util.exec_cmd(cmd1, shell=True)
        if ret1:
            logger.error("random code generated fail.")
            return False

        cmd2 = "mkdir /tmp/%s && touch /tmp/%s/$(uuidgen|cut -d- -f1)" \
                                                   % (out1, out1)
        ret2, out2 = util.exec_cmd(cmd2, shell=True)
        if ret2:
            logger.error("fail to create files for iso image: \n %s" % out1)
            return False
        else:
            logger.info("prepare files for iso image creation.")

        cmd3 = "genisoimage -o %s /tmp/%s" % (img_name, out1)
        ret3, out3 = util.exec_cmd(cmd3, shell=True)
        if ret3:
            logger.error("iso file creation fail: \n %s" % out1)
            return False
        else:
            logger.info("create an image: %s" % img_name)

    elif params['devtype'] == 'floppy':
        cmd1 = "dd if=/dev/zero of=%s bs=1440k count=1" % img_name
        ret1, out1 = util.exec_cmd(cmd1, shell=True)
        if ret1:
            logger.error("floppy image creation fail: \n %s" % out1)
            return False
        else:
            logger.info("create an image for floppy use: %s" % img_name)

        cmd2 = "mkfs.msdos -s 1 %s" % img_name
        ret2, out2 = util.exec_cmd(cmd2, shell=True)
        if ret2:
            logger.error("fail to format image: \n %s" % out2)
            return False
        else:
            logger.info("succeed to format image: %s" % img_name)

        cmd3 = "mount -o loop %s /mnt && touch /mnt/$(uuidgen|cut -d- -f1) \
                                      && umount -l /mnt" % img_name
        ret3, out3 = util.exec_cmd(cmd3, shell=True)
        if ret3:
            logger.error("fail to write file to floppy image: \n %s" % out3)
            return False
        else:
            logger.info("succeed to write file to floopy image: %s" % img_name)

    else:
        logger.error("wrong device type was specified.")
        return False

    return True

def check_device_in_guest(params, util, guestip):
    """Check updated device in guest"""
    logger = params['logger']

    if params['devtype'] == 'cdrom':
        cmd = "mount -o loop /dev/cdrom /media"
    elif params['devtype'] == 'floppy':
        cmd = "mount /dev/fd0 /media"
    else:
        logger.error("it's not a cdrom or floppy device.")
        return False, None

    ret, output = util.remote_exec_pexpect(guestip, params['username'], \
                                               params['password'], cmd)
    logger.debug(output)
    if ret:
        logger.error("failed to mount %s device." % params['devtype'])
        return False, output

    time.sleep(5)

    ret, output = util.remote_exec_pexpect(guestip, params['username'], \
                                           params['password'], "umount /media")
    logger.debug(output)
    if ret:
        logger.error("failed to unmount %s device." % params['devtype'])
        return False, output

    time.sleep(5)

    ret, output = util.remote_exec_pexpect(guestip, params['username'], \
                                           params['password'], "ls /media")
    logger.debug(output)
    if ret:
        logger.error("failed to list contents of %s device." \
                                           % params['devtype'])
        return False, output

    return True, output

def check_updated_device(params, output, util, guestip, domobj, srcfile):
    """Check if the device is updated"""
    logger = params['logger']
    xmlobj = domobj.XMLDesc(0)
    domxml = minidom.parseString(xmlobj)

    for diskTag in domxml.getElementsByTagName("source"):
        if diskTag.parentNode.getAttribute("device") == 'cdrom':
            upfile = diskTag.getAttribute("file")
        elif diskTag.parentNode.getAttribute('device') == 'floppy':
            upfile = diskTag.getAttribute("file")

    res = check_device_in_guest(params, util, guestip)
    if res[0] and cmp(res[1], output):
        if upfile == srcfile:
            logger.debug("checking fail.")
            return False, upfile
        else:
            logger.debug("checking successful.")
            return True, upfile
    else:
        return False, upfile

def update_devflag(params):
    """Update virtual device to a domain from xml"""
    util = utils.Utils()

    # Initiate and check parameters
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    logger = params['logger']
    guestname = params['guestname']
    devtype = params['devtype']

    if devtype == 'cdrom':
        xmlargs = {}
        xmlargs['guestname'] = guestname
        xmlargs['guesttype'] = 'kvm'
        xmlargs['hdmodel'] = 'ide'
        xmlargs['bootcd'] = '/var/lib/libvirt/boot/cdrom.img'
        srcfile = xmlargs['bootcd']
        if not create_image(params, util, srcfile):
            return 1
    elif devtype == 'floppy':
        xmlargs = {}
        xmlargs['guestname'] = guestname
        xmlargs['floppysource'] = '/var/lib/libvirt/boot/floppy.img'
        srcfile = xmlargs['floppysource']
        if not create_image(params, util, srcfile):
            return 1
    else:
        srcfile = None
        logger.error("Wrong device type was specified.")
        return 1

    if not params.has_key('flag'):
        flag = libvirt.VIR_DOMAIN_AFFECT_CONFIG

    # Connect to local hypervisor connection URI
    uri = params['uri']
    mac = util.get_dom_mac_addr(guestname)
    guestip = util.mac_to_ip(mac, 180)
    logger.debug("ip address: %s" % guestip)

    conn = libvirt.open(uri)

    try:
        if guestname not in conn.listDefinedDomains():
            logger.error("%s doesn't exist or in running state." % guestname)
            return 1
        else:
            domobj = conn.lookupByName(guestname)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    guestxml = domobj.XMLDesc(0)
    guestobj = minidom.parseString(guestxml)

    # Generat device XML for original use
    origxmlobj = xmlbuilder.XmlBuilder()

    if devtype == 'cdrom':
        origxmlobj.add_cdrom(xmlargs, guestobj)
        guestxml = origxmlobj.build_domain(guestobj)
    elif devtype == 'floppy':
        origxmlobj.add_floppy(xmlargs, guestobj)
        guestxml = origxmlobj.build_domain(guestobj)

    try:
        domobj.undefine()
        conn.defineXML(guestxml)
        domobj.create()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    time.sleep(60)
    ret, output = check_device_in_guest(params, util, guestip)
    logger.debug(output)
    if not ret:
        return 1

    # Generate device XML for updating
    newxmlobj = xmlbuilder.XmlBuilder()

    if devtype == 'cdrom':
        xmlargs['bootcd'] = '/var/lib/libvirt/boot/cdrom-new.img'
        upfile = xmlargs['bootcd']
        if not create_image(params, util, upfile):
            logger.info("fail to create new image.")
            return 1
        newdevxml = newxmlobj.build_cdrom(xmlargs)
    elif devtype == 'floppy':
        xmlargs['floppysource'] = '/var/lib/libvirt/boot/floppy-new.img'
        upfile = xmlargs['floppysource']
        if not create_image(params, util, upfile):
            logger.info("fail to create new image.")
            return 1
        newdevxml = newxmlobj.build_floppy(xmlargs)

    logger.debug("block device xml desc for update:\n%s" % newdevxml)

    logger.debug("domain xml before updating:\n%s" \
                                   % domobj.XMLDesc(0))

    try:
        domobj.updateDeviceFlags(newdevxml, 0)
        logger.debug("domain xml after updating:\n%s" \
                                   % domobj.XMLDesc(0))
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    result = check_updated_device(params, output, util, \
                                       guestip, domobj, srcfile)
    if result[0]:
        logger.error("fail to update '%s' device: %s\n" % (devtype, result[1]))
        conn.close()
        return 1

    logger.info("success to update '%s' device: %s\n" % (devtype, result[1]))
    conn.close()
    return 0

def update_devflag_clean(params):
    """Clean testing environment"""
    logger = params['logger']

    if params['devtype'] == 'cdrom':
        os.unlink('/var/lib/libvirt/boot/cdrom.img')
        os.unlink('/var/lib/libvirt/boot/cdrom-new.img')
    elif params['devtype'] == 'floppy':
        os.unlink('/var/lib/libvirt/boot/floppy.img')
        os.unlink('/var/lib/libvirt/boot/floppy-new.img')
    else:
        logger.debug("image file does not exist or has been already removed.")
