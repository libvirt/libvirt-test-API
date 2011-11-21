#!/usr/bin/env python
"""This test is for start a guest with img file on nfs storage.
   Under SElinux boolean virt_use_nfs on or off, combine with
   setting the dynamic_ownership in /etc/libvirt/qemu.conf,
   check whether the guest can be started or not. The nfs could
   be root_squash or no_root_squash. SElinux should be enabled
   and enforcing on host.
   sVirt:domain_nfs_start
       guestname
           #GUESTNAME#
       dynamic_ownership
           enable|disable
       virt_use_nfs
           on|off
       root_squash
           yes|no
"""

__author__ = 'Wayne Sun: gsun@redhat.com'
__date__ = 'Mon Sep 2, 2011'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2011 Red Hat, Inc.'
__all__ = ['domain_nfs_start']

import os
import re
import sys

QEMU_CONF = "/etc/libvirt/qemu.conf"

def append_path(path):
    """Append root path of package"""
    if path not in sys.path:
        sys.path.append(path)

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI
from shutil import copy

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

def return_close(conn, logger, ret):
    """close hypervisor connection and return the given value"""
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'dynamic_ownership', 'virt_use_nfs', 'root_squash']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
    return 0

def nfs_setup(util, root_squash, logger):
    """setup nfs on localhost
    """
    logger.info("set nfs service")
    if root_squash == "yes":
        option = "root_squash"
    elif root_squash == "no":
        option = "no_root_squash"
    else:
        logger.error("wrong root_squash value")
        return 1

    cmd = "echo /tmp *\(rw,%s\) >> /etc/exports" % option
    ret, out = util.exec_cmd(cmd, shell=True)
    if ret:
        logger.error("failed to config nfs export")
        return 1

    logger.info("restart nfs service")
    cmd = "service nfs restart"
    ret, out = util.exec_cmd(cmd, shell=True)
    if ret:
        logger.error("failed to restart nfs service")
        return 1
    else:
        for i in range(len(out)):
            logger.info(out[i])

    return 0

def prepare_env(util, d_ownership, virt_use_nfs, guestname, root_squash, \
                disk_file, img_dir, logger):
    """set virt_use_nfs SElinux boolean, configure
       dynamic_ownership in /etc/libvirt/qemu.conf
    """
    logger.info("set virt_use_nfs selinux boolean")
    cmd = "setsebool virt_use_nfs %s" % virt_use_nfs
    ret, out = util.exec_cmd(cmd, shell=True)
    if ret:
        logger.error("failed to set virt_use_nfs SElinux boolean")
        return 1

    logger.info("set the dynamic ownership in %s as %s" % \
                (QEMU_CONF, d_ownership))
    if d_ownership == "enable":
        option = 1
    elif d_ownership == "disable":
        option = 0
    else:
        logger.error("wrong dynamic_ownership value")
        return 1

    set_cmd = "echo dynamic_ownership = %s >> %s" % \
               (option, QEMU_CONF)
    ret, out = util.exec_cmd(set_cmd, shell=True)
    if ret:
        logger.error("failed to set dynamic ownership")
        return 1

    logger.info("restart libvirtd")
    restart_cmd = "service libvirtd restart"
    ret, out = util.exec_cmd(restart_cmd, shell=True)
    if ret:
        logger.error("failed to restart libvirtd")
        for i in range(len(out)):
            logger.info(out[i])
        return 1
    else:
        for i in range(len(out)):
            logger.info(out[i])

    file_name = os.path.basename(disk_file)
    filepath = "/tmp/%s" % file_name
    if os.path.exists(filepath):
        os.remove(filepath)

    logger.info("copy %s img file to nfs path" % guestname)
    copy(disk_file, "/tmp")

    logger.info("set up nfs service on localhost")
    ret = nfs_setup(util, root_squash, logger)
    if ret:
        return 1

    logger.info("mount nfs to img dir path")
    mount_cmd = "mount -o vers=3 127.0.0.1:/tmp %s" % img_dir
    ret, out = util.exec_cmd(mount_cmd, shell=True)
    if ret:
        logger.error("Failed to mount the nfs path")
        for i in range(len(out)):
            logger.info(out[i])
        return 1

    return 0

def domain_nfs_start(params):
    """start domain with img on nfs"""
    # Initiate and check parameters
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    logger = params['logger']
    guestname = params['guestname']
    dynamic_ownership = params['dynamic_ownership']
    virt_use_nfs = params['virt_use_nfs']
    root_squash = params['root_squash']

    util = utils.Utils()

    # Connect to local hypervisor connection URI
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)

    logger.info("get the domain state")
    try:
        state = domobj.get_state(guestname)
        logger.info("domain %s is %s" % (guestname, state))
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to get domain %s state" % guestname)
        return return_close(conn, logger, 1)

    if state != "shutoff":
        logger.info("shut down the domain %s" % guestname)
        try:
            domobj.destroy(guestname)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" % \
                          (e.response()['message'], e.response()['code']))
            logger.error("Error: fail to destroy domain %s" % guestname)
            return return_close(conn, logger, 1)

    logger.info("get guest img file path")
    try:
        dom_xml = domobj.get_xml_desc(guestname)
        disk_file = util.get_disk_path(dom_xml)
        logger.info("%s disk file path is %s" % (guestname, disk_file))
        img_dir = os.path.dirname(disk_file)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to get domain %s xml" % guestname)
        return return_close(conn, logger, 1)

    # close connection before restart libvirtd
    conn.close()

    # set env
    logger.info("prepare the environment")
    ret = prepare_env(util, dynamic_ownership, virt_use_nfs, guestname, \
                      root_squash, disk_file, img_dir, logger)
    if ret:
        logger.error("failed to prepare the environment")
        return return_close(conn, logger, 1)

    # reconnect
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)

    logger.info("begin to test start domain from nfs storage")
    logger.info("First, start the domain without chown the img file to qemu")
    logger.info("start domain %s" % guestname)
    if root_squash == "yes":
        if virt_use_nfs == "on":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)
        elif virt_use_nfs == "off":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)
    elif root_squash == "no":
        if virt_use_nfs == "on":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.info("Success start domain %s" % guestname)
                except LibvirtAPI, e:
                    logger.error("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.error("Fail to start domain %s" % guestname)
                    return return_close(conn, logger, 1)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)
        elif virt_use_nfs == "off":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

    logger.info("get the domain state")
    try:
        state = domobj.get_state(guestname)
        logger.info("domain %s is %s" % (guestname, state))
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to get domain %s state" % guestname)
        return return_close(conn, logger, 1)

    if state != "shutoff":
        logger.info("shut down the domain %s" % guestname)
        try:
            domobj.destroy(guestname)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" % \
                          (e.response()['message'], e.response()['code']))
            logger.error("Error: fail to destroy domain %s" % guestname)
            return return_close(conn, logger, 1)

    logger.info("Second, start the domain after chown the img file to qemu")

    file_name = os.path.basename(disk_file)
    filepath = "/tmp/%s" % file_name
    logger.info("set chown of %s as 107:107" % filepath)
    chown_cmd = "chown 107:107 %s" % filepath
    ret, out = util.exec_cmd(chown_cmd, shell=True)
    if ret:
        logger.error("failed to chown %s to qemu:qemu" % filepath)
        return return_close(conn, logger, 1)

    logger.info("start domain %s" % guestname)
    if root_squash == "yes":
        if virt_use_nfs == "on":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.info("Success start domain %s" % guestname)
                except LibvirtAPI, e:
                    logger.error("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.error("Fail to start domain %s" % guestname)
                    return return_close(conn, logger, 1)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.info("Success start domain %s" % guestname)
                except LibvirtAPI, e:
                    logger.error("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.error("Fail to start domain %s" % guestname)
                    return return_close(conn, logger, 1)

        elif virt_use_nfs == "off":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)
    elif root_squash == "no":
        if virt_use_nfs == "on":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.info("Success start domain %s" % guestname)
                except LibvirtAPI, e:
                    logger.error("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.error("Fail to start domain %s" % guestname)
                    return return_close(conn, logger, 1)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.info("Success start Domain %s" % guestname)
                except LibvirtAPI, e:
                    logger.error("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.error("Fail to start domain %s" % guestname)
                    return return_close(conn, logger, 1)

        elif virt_use_nfs == "off":
            if dynamic_ownership == "enable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

            elif dynamic_ownership == "disable":
                try:
                    domobj.start(guestname)
                    logger.error("Domain %s started, this is not expected" % \
                                  guestname)
                    return return_close(conn, logger, 1)
                except LibvirtAPI, e:
                    logger.info("API error message: %s, error code is %s" % \
                                  (e.response()['message'], e.response()['code']))
                    logger.info("Fail to start domain %s, this is expected" % \
                                 guestname)

    return return_close(conn, logger, 0)

def domain_nfs_start_clean(params):
    """clean testing environment"""
    logger = params['logger']
    guestname = params['guestname']

    util = utils.Utils()

    # Connect to local hypervisor connection URI
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)

    if domobj.get_state(guestname) != "shutoff":
        domobj.destroy(guestname)

    dom_xml = domobj.get_xml_desc(guestname)
    disk_file = util.get_disk_path(dom_xml)
    img_dir = os.path.dirname(disk_file)
    file_name = os.path.basename(disk_file)
    temp_file = "/tmp/%s" % file_name

    if os.path.ismount(img_dir):
        umount_cmd = "umount -f %s" % img_dir
        ret, out = util.exec_cmd(umount_cmd, shell=True)
        if ret:
            logger.error("failed to umount %s" % img_dir)

    if os.path.exists(temp_file):
        os.remove(temp_file)

    conn.close()

    clean_nfs_conf = "sed -i '$d' /etc/exports"
    util.exec_cmd(clean_nfs_conf, shell=True)

    clean_qemu_conf = "sed -i '$d' %s" % QEMU_CONF
    util.exec_cmd(clean_qemu_conf, shell=True)

    cmd = "service libvirtd restart"
    util.exec_cmd(cmd, shell=True)

    return 0
