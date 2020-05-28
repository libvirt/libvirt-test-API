# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# Install a linux domain from pxe

import os
import time
import shutil

from libvirttestapi.src import sharedmod
from libvirttestapi.repos.installation import install_common
from libvirttestapi.utils import utils, process

required_params = ('guestname', 'guestos', 'guestarch',)
optional_params = {'memory': 4194304,
                   'vcpu': 2,
                   'disksize': 14,
                   'diskpath': '/var/lib/libvirt/images/libvirt-test-api',
                   'imageformat': 'qcow2',
                   'hddriver': 'virtio',
                   'nicdriver': 'virtio',
                   'macaddr': '52:54:00:97:e4:28',
                   'type': 'define',
                   'xml': 'xmls/install_pxe.xml',
                   'graphic': "spice",
                   'video': 'qxl',
                   'guestmachine': 'pc',
                   'rhelnewest': '', }

VIRSH_QUIET_LIST = "virsh --quiet list --all|awk '{print $2}'|grep \"^%s$\""
VM_STAT = "virsh --quiet list --all| grep \"\\b%s\\b\"|grep off"
VM_DESTROY = "virsh destroy %s"
VM_UNDEFINE = "virsh undefine %s"

HOME_PATH = utils.get_base_path()

TFTPPATH = "/var/lib/tftpboot"


def clean_env(diskpath, logger):
    if os.path.exists(diskpath):
        os.remove(diskpath)

    if os.path.exists(TFTPPATH + '/pxelinux.cfg/default'):
        os.remove(TFTPPATH + '/pxelinux.cfg/default')

    cmd = "virsh net-list --all | grep \'pxeboot\'"
    ret = process.run(cmd, shell=True, ignore_status=True)
    if not ret.exit_status:
        logger.info("remove network pxeboot")
        cmd = "virsh net-destroy pxeboot"
        ret = process.run(cmd, shell=True, ignore_status=True)
        if ret.exit_status:
            logger.error("failed to destroy network pxeboot")
            logger.error("%s" % ret.stdout)
        else:
            cmd = "virsh net-undefine pxeboot"
            ret = process.run(cmd, shell=True, ignore_status=True)
            if ret.exit_status:
                logger.error("failed to undefine network pxeboot")
                logger.error("%s" % ret.stdout)


def prepare_install(default_file, logger):
    if not os.path.exists(TFTPPATH + "/pxelinux.cfg"):
        logger.info("%s not exists, create it" % (TFTPPATH + "/pxelinux.cfg"))
        os.makedirs(TFTPPATH + "/pxelinux.cfg", mode=0o777)
    else:
        os.chmod(TFTPPATH + "/pxelinux.cfg", 0o777)
    # Get rid of selinux problem
    os.system("restorecon -Rv %s" % TFTPPATH)
    bootp_file = TFTPPATH + "/pxelinux.0"
    if not os.path.exists(bootp_file):
        shutil.copy("/usr/share/syslinux/pxelinux.0", TFTPPATH)

    cmd = "wget " + default_file + " -P " + TFTPPATH + "/pxelinux.cfg/"
    logger.info("%s" % cmd)
    ret = process.run(cmd, shell=True, ignore_status=True)

    xmlpath = os.path.join(HOME_PATH, 'xmls/installation/pxeboot.xml')
    cmd = "virsh net-define %s" % xmlpath
    logger.info("%s" % cmd)
    ret = process.run(cmd, shell=True, ignore_status=True)

    cmd = "virsh net-start pxeboot"
    logger.info("%s" % cmd)
    ret = process.run(cmd, shell=True, ignore_status=True)


def install_linux_pxe(params):
    """ install a new virtual machine """
    logger = params['logger']

    guestname = params.get('guestname')
    guestos = params.get('guestos')
    guestarch = params.get('guestarch')
    xmlstr = params['xml']
    nicdriver = params.get('nicdriver', 'virtio')
    hddriver = params.get('hddriver', 'virtio')
    diskpath = params.get('diskpath', '/var/lib/libvirt/images/libvirt-test-api')
    imageformat = params.get('imageformat', 'qcow2')
    seeksize = params.get('disksize', 14)
    graphic = params.get('graphic', 'spice')
    video = params.get('video', 'qxl')
    installtype = params.get('type', 'define')
    rhelnewest = params.get('rhelnewest')
    guestmachine = params.get('guestmachine', 'pc')

    options = [guestname, guestos, guestarch, nicdriver, hddriver, imageformat, graphic, video, diskpath, seeksize, "local"]
    logger.info("rhelnewest: %s" % rhelnewest)
    install_common.prepare_env(options, logger)

    clean_env(diskpath, logger)
    install_common.create_image(diskpath, seeksize, imageformat, logger)

    xmlstr = xmlstr.replace('GRAPHIC', graphic)
    xmlstr = xmlstr.replace('GUESTMACHINE', guestmachine)
    xmlstr = install_common.set_disk_xml(hddriver, xmlstr, diskpath, logger)
    xmlstr = install_common.set_video_xml(video, xmlstr)

    os_arch = guestos + "_" + guestarch
    if rhelnewest is None:
        default_file = utils.get_value_from_global("guest", os_arch + "_pxe_default")
    else:
        release_ver_list = utils.get_value_from_global("other", "release_ver").split()
        location = utils.get_local_hostname()
        if "pek2" in location or "nay" in location:
            if "RHEL-ALT" in rhelnewest:
                version = rhelnewest.split("/")[6].split("-")[2]
            else:
                version = rhelnewest.split("/")[6].split("-")[1]
        else:
            if "RHEL-ALT" in rhelnewest:
                version = rhelnewest.split("/")[4].split("-")[2]
            else:
                version = rhelnewest.split("/")[6].split("-")[1]
        release_ver_flag = 0
        for release_ver in release_ver_list:
            if version == release_ver:
                release_ver_flag = 1
        if release_ver_flag:
            default_file = utils.get_value_from_global("guest", os_arch + "_pxe_default")
        else:
            default_file = utils.get_value_from_global("guest", "rhel%s_newest_%s_pxe_default" %
                                                                (version.split(".")[0], guestarch))

    logger.debug('default file:\n    %s' % default_file)

    logger.info("begin to prepare network")
    prepare_install(default_file, logger)

    logger.debug('dump installation guest xml:\n%s' % xmlstr)

    conn = sharedmod.libvirtobj['conn']
    if not install_common.start_guest(conn, installtype, xmlstr, logger):
        logger.error("fail to define domain %s" % guestname)
        return 1

    if not install_common.wait_install(conn, guestname, xmlstr, installtype, "pxe", logger):
        return 1

    time.sleep(60)

    return 0


def install_linux_pxe_clean(params):
    """ clean testing environment """
    logger = params['logger']
    guestname = params.get('guestname')
    diskpath = params.get('diskpath', '/var/lib/libvirt/images/libvirt-test-api')
    install_common.clean_guest(guestname, logger)
    clean_env(diskpath, logger)
