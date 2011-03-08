#!/usr/bin/env python
"""The test script is for installing a new windows guest virtual machine
   via calling libvirt python bindings API.
   mandatory arguments:guesttype
                       guestname
                       guestos
                       guestarch
   optional arguments: memory
                       vcpu
                       disksize
                       imagepath
                       hdmodel
                       nicmodel
                       macaddr
                       ifacetype
                       source
                       volumepath
                       type: define|create
"""

import os
import sys
import re
import time
import copy
import commands
import shutil

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
homepath = result.group(0)
append_path(homepath)

from lib.Python import connectAPI
from lib.Python import domainAPI
from utils.Python import utils
from utils.Python import env_parser
from utils.Python import xmlbuilder
from exception import LibvirtAPI

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Jun 29 2010"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2010 Red Hat, Inc."
__all__ = ['install_windows_cdrom', 'usage']

def usage():
    print '''usage: mandatory arguments:guesttype
                           guestname
                           guestos
                           guestarch
       optional arguments: memory
                           vcpu
                           disksize
                           imagepath
                           hdmodel
                           nicmodel
                           macaddr
                           ifacetype
                           source
                           volumepath
                           type: define|create
          '''

def check_params(params):
    """Checking the arguments required"""
    params_given = copy.deepcopy(params)
    mandatory_args = ['guestname', 'guesttype', 'guestos', 'guestarch']
    optional_args = ['memory', 'vcpu', 'disksize', 'imagepath', 'hdmodel',
                     'nicmodel', 'macaddr', 'ifacetype', 'source', 'type',
                     'volumepath']

    for arg in mandatory_args:
        if arg not in params_given.keys():
            logger.error("Argument %s is required." % arg)
            usage()
            return 1
        elif not params_given[arg]:
            logger.error("value of argument %s is empty." % arg)
            usage()
            return 1

        params_given.pop(arg)

    if len(params_given) == 0:
        return 0

    for arg in params_given.keys():
        if arg not in optional_args:
            logger.error("Argument %s could not be recognized." % arg)
            return 1

    return 0

def cleanup(mount):
    """Clean up a previously used mountpoint.
       @param mount: Mountpoint to be cleaned up.
    """
    if os.path.isdir(mount):
        if os.path.ismount(mount):
            logger.error("Path %s is still mounted, please verify" % mount)
        else:
            logger.info("Removing mount point %s" % mount)
            os.rmdir(mount)

def prepare_iso(iso_file, mount_point):
    """Mount windows nfs server to /mnt/libvirt_windows
       return windows iso absolute path
    """
    # download iso_file into /tmp
    windows_iso = iso_file.split('/')[-1]
    download_cmd = "wget -P /tmp %s" % iso_file
    (status, text) = commands.getstatusoutput(download_cmd)
    if status:
        logger.error("failed to download windows iso file")
        return 1, None

    iso_local_path = os.path.join("/tmp", windows_iso)

    return 0, iso_local_path

def prepare_floppy_image(guestname, guestos, guestarch,
                         windows_unattended_path, cdkey, floppy_img):
    """Making corresponding floppy images for the given guestname
    """
    if os.path.exists(floppy_img):
        os.remove(floppy_img)

    create_cmd = 'dd if=/dev/zero of=%s bs=1440k count=1' % floppy_img
    (status, text) = commands.getstatusoutput(create_cmd)
    if status:
        logger.error("failed to create floppy image")
        return 1

    format_cmd = 'mkfs.msdos -s 1 %s' % floppy_img
    (status, text) = commands.getstatusoutput(format_cmd)
    if status:
        logger.error("failed to format floppy image")
        return 1

    floppy_mount = "/mnt/libvirt_floppy"
    if os.path.exists(floppy_mount):
        logger.info("the floppy mount point folder exists, remove it")
        shutil.rmtree(floppy_mount)

    logger.info("create mount point %s" % floppy_mount)
    os.makedirs(floppy_mount)

    try:
        mount_cmd = 'mount -o loop %s %s' % (floppy_img, floppy_mount)
        (status, text) = commands.getstatusoutput(mount_cmd)
        if status:
            logger.error(
            "failed to mount /tmp/floppy.img to /mnt/libvirt_floppy")
            return 1

        if '2008' in guestos or '7' in guestos or 'vista' in guestos:
            dest_fname = "autounattend.xml"
            source = os.path.join(windows_unattended_path, "%s_%s.xml" %
                                 (guestos, guestarch))

        elif '2003' in guestos or 'xp' in guestos:
            dest_fname = "winnt.sif"
            setup_file = 'winnt.bat'
            setup_file_path = os.path.join(windows_unattended_path, setup_file)
            setup_file_dest = os.path.join(floppy_mount, setup_file)
            shutil.copyfile(setup_file_path, setup_file_dest)
            source = os.path.join(windows_unattended_path, "%s_%s.sif" %
                                  (guestos, guestarch))

        dest = os.path.join(floppy_mount, dest_fname)

        unattended_contents = open(source).read()
        dummy_cdkey_re = r'\bLIBVIRT_TEST_CDKEY\b'
        if re.search(dummy_cdkey_re, unattended_contents):
            unattended_contents = re.sub(dummy_cdkey_re, cdkey,
                                         unattended_contents)

        logger.debug("Unattended install %s contents:" % dest_fname)
        logger.debug(unattended_contents)

        open(dest, 'w').write(unattended_contents)

    finally:
        umount_cmd = 'umount %s' % floppy_mount
        (status, text) = commands.getstatusoutput(umount_cmd)
        if status:
            logger.error("failed to umount %s" % floppy_mount)
            return 1

        cleanup(floppy_mount)

    os.chmod(floppy_img, 0755)
    logger.info("Boot floppy created successfuly")

    return 0

def prepare_boot_guest(domobj, dict, installtype):
    """ After guest installation is over, undefine the guest with
        bootting off cdrom, to define the guest to boot off harddisk.
    """
    params = copy.deepcopy(dict)

    guestname = params['guestname']

    xmlobj = xmlbuilder.XmlBuilder()
    domain = xmlobj.add_domain(params)

    xmlobj.add_disk(params, domain)
    xmlobj.add_interface(params, domain)
    guestxml = xmlobj.build_domain(domain)

    if installtype != 'create':
        domobj.undefine(guestname)
        logger.info("undefine %s : \n" % guestname)

    try:
        domobj.define(guestxml)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to define domain %s" % guestname)
        return 1

    logger.info("define guest %s " % guestname)
    logger.debug("the xml description of guest booting off harddisk is %s" %
                 guestxml)

    logger.info('boot guest up ...')

    try:
        domobj.start(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to start domain %s" % guestname)
        return 1

    return 0

def install_windows_cdrom(params):
    """ install a windows guest virtual machine by using iso file """
    # Initiate and check parameters
    global logger
    logger = params['logger']
    params.pop('logger')
    logger.info("Checking the validation of arguments provided.")
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    logger.info("Arguments checkup finished.")

    guestname = params.get('guestname')
    guesttype = params.get('guesttype')
    guestos = params.get('guestos')
    guestarch = params.get('guestarch')

    logger.info("the name of guest is %s" % guestname)
    logger.info("the type of guest is %s" % guesttype)

    util = utils.Utils()
    hypervisor = util.get_hypervisor()

    if not params.has_key('macaddr'):
        macaddr = util.get_rand_mac()
        params['macaddr'] = macaddr

    uri = util.get_uri('127.0.0.1')

    logger.info("the macaddress is %s" % params['macaddr'])
    logger.info("the type of hypervisor is %s" % hypervisor)
    logger.debug("the uri to connect is %s" % uri)

    if params.has_key('imagepath') and not params.has_key('volumepath'):
        imgfullpath = os.join.path(params.get('imagepath'), guestname)
    elif not params.has_key('imagepath') and not params.has_key('volumepath'):
        if hypervisor == 'xen':
            imgfullpath = os.path.join('/var/lib/xen/images', guestname)
        elif hypervisor == 'kvm':
            imgfullpath = os.path.join('/var/lib/libvirt/images', guestname)
    elif not params.has_key('imagepath') and params.has_key('volumepath'):
        imgfullpath = params['volumepath']

    else:
        logger.error(
        "we could only choose one between imagepath and volumepath")
        return 1

    params['fullimagepath'] = imgfullpath

    logger.info("the path of directory of disk images located on is %s" %
                imgfullpath)

    if params.has_key('disksize'):
        seeksize = params.get('disksize')
    else:
        seeksize = '20'

    logger.info("the size of disk image is %sG" % (seeksize))
    shell_disk_dd = "dd if=/dev/zero of=%s bs=1 count=1 seek=%sG" % \
                    (imgfullpath, seeksize)
    logger.debug("the commands line of creating disk images is '%s'" %
                 shell_disk_dd)

    (status, message) = commands.getstatusoutput(shell_disk_dd)

    if status != 0:
        logger.debug(message)
    else:
        logger.info("creating disk images file is successful.")

    logger.info("get system environment information")
    envfile = os.path.join(homepath, 'env.cfg')
    logger.info("the environment file is %s" % envfile)

    # Get iso file based on guest os and arch from env.cfg
    envpaser = env_parser.Envpaser(envfile)
    iso_file = envpaser.get_value("guest", guestos + '_' + guestarch)
    cdkey = envpaser.get_value("guest", "%s_%s_key" % (guestos, guestarch))

    windows_unattended_path = os.path.join(homepath,
                              "repos/Python/domain/windows_unattended")

    logger.debug('install source: \n    %s' % iso_file)

    logger.info('prepare pre-installation environment...')
    logger.info('mount windows nfs server to /mnt/libvirt_windows')

    iso_mount_point = "/mnt/libvirt_windows"

    status, iso_local_path = prepare_iso(iso_file, iso_mount_point)
    if status:
        logger.error("installation failed")
        return 1
    params['bootcd'] = iso_local_path

    floppy_img = "/tmp/floppy.img"

    status = prepare_floppy_image(guestname, guestos, guestarch,
                                  windows_unattended_path, cdkey, floppy_img)
    if status:
        logger.error("making floppy image failed")
        return 1
    params['floppysource'] = floppy_img

    xmlobj = xmlbuilder.XmlBuilder()
    guestxml = xmlobj.build_domain_install_win(params)
    logger.debug('dump installation guest xml:\n%s' % guestxml)

    # Generate guest xml
    virconn = connectAPI.ConnectAPI().open(uri)
    domobj = domainAPI.DomainAPI(virconn)
    installtype = params.get('type')
    if installtype == None or installtype == 'define':
        logger.info('define guest from xml description')
        try:
            domobj.define(guestxml)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" %
                         (e.response()['message'], e.response()['code']))
            logger.error("fail to define domain %s" % guestname)
            return 1

        logger.info('start installation guest ...')

        try:
            domobj.start(guestname)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" %
                         (e.response()['message'], e.response()['code']))
            logger.error("fail to start domain %s" % guestname)
            return 1
    elif installtype == 'create':
        logger.info('create guest from xml description')
        try:
            domobj.create(guestxml)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" %
                         (e.response()['message'], e.response()['code']))
            logger.error("fail to define domain %s" % guestname)
            return 1

    interval = 0
    while(interval < 7200):
        time.sleep(20)
        if installtype == None or installtype == 'define':
            state = domobj.get_state(guestname)
            if(state == "shutoff"):
                logger.info("guest installaton of define type is complete.")
                logger.info("boot guest vm off harddisk")
                ret  = prepare_boot_guest(domobj, params, installtype)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return 1
                break
            else:
                interval += 20
                logger.info('%s seconds passed away...' % interval)
        elif installtype == 'create':
            dom_name_list = domobj.get_list()
            if guestname not in dom_name_list:
                logger.info("guest installation of create type is complete.")
                logger.info("define the vm and boot it up")
                ret = prepare_boot_guest(domobj, params, installtype)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return 1
                break
            else:
                interval += 20
                logger.info('%s seconds passed away...' % interval)

    if interval == 7200:
        logger.info("guest installation timeout 7200s")
        return 1
    else:
        logger.info("guest is booting up")

    logger.info("get the mac address of vm %s" % guestname)
    mac = util.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 600

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = util.mac_to_ip(mac, 180)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % guestname)
            logger.info("the ip address of vm %s is %s" % (guestname, ip))

            break

    if timeout == 0:
        logger.info("fail to power on vm %s" % guestname)
        return 1

    time.sleep(60)

    return 0
