#!/usr/bin/env python
# Install a Windows domain

import os
import sys
import re
import time
import copy
import commands
import shutil

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import env_parser
from utils import xmlbuilder

VIRSH_QUIET_LIST = "virsh --quiet list --all|awk '{print $2}'|grep \"^%s$\""
VM_STAT = "virsh --quiet list --all| grep \"\\b%s\\b\"|grep off"
VM_DESTROY = "virsh destroy %s"
VM_UNDEFINE = "virsh undefine %s"

FLOOPY_IMG = "/tmp/floppy.img"
ISO_MOUNT_POINT = "/mnt/libvirt_windows"
HOME_PATH = os.getcwd()

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Checking the arguments required"""
    params_given = copy.deepcopy(params)
    mandatory_args = ['guestname', 'guesttype', 'guestos', 'guestarch']
    optional_args = ['uuid', 'memory', 'vcpu', 'disksize', 'imagepath',
                     'hdmodel', 'nicmodel', 'macaddr', 'ifacetype',
                     'source', 'type', 'volumepath', 'imagetype']

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
                         windows_unattended_path, cdkey, FLOOPY_IMG):
    """Making corresponding floppy images for the given guestname
    """
    if os.path.exists(FLOOPY_IMG):
        os.remove(FLOOPY_IMG)

    create_cmd = 'dd if=/dev/zero of=%s bs=1440k count=1' % FLOOPY_IMG
    (status, text) = commands.getstatusoutput(create_cmd)
    if status:
        logger.error("failed to create floppy image")
        return 1

    format_cmd = 'mkfs.msdos -s 1 %s' % FLOOPY_IMG
    (status, text) = commands.getstatusoutput(format_cmd)
    if status:
        logger.error("failed to format floppy image")
        return 1

    floppy_mount = "/mnt/libvirt_floppy"
    if os.path.exists(floppy_mount):
        logger.info("the floppy mount point folder exists, remove it")
        shutils.rmtree(floppy_mount)

    logger.info("create mount point %s" % floppy_mount)
    os.makedirs(floppy_mount)

    try:
        mount_cmd = 'mount -o loop %s %s' % (FLOOPY_IMG, floppy_mount)
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
            shutils.copyfile(setup_file_path, setup_file_dest)
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

    os.chmod(FLOOPY_IMG, 0755)
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
        domobj.undefine()
        logger.info("undefine %s : \n" % guestname)

    try:
        conn = domobj._conn
        domobj = conn.defineXML(guestxml)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to define domain %s" % guestname)
        return 1

    logger.info("define guest %s " % guestname)
    logger.debug("the xml description of guest booting off harddisk is %s" %
                 guestxml)

    logger.info('boot guest up ...')

    try:
        domobj.create()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to start domain %s" % guestname)
        return 1

    return 0

def install_windows_cdrom(params):
    """ install a windows guest virtual machine by using iso file """
    # Initiate and check parameters
    global logger
    logger = params['logger']
    params.pop('logger')
    uri = params['uri']
    params.pop('uri')

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

    hypervisor = utils.get_hypervisor()

    if not params.has_key('macaddr'):
        macaddr = utils.get_rand_mac()
        params['macaddr'] = macaddr

    logger.info("the macaddress is %s" % params['macaddr'])
    logger.info("the type of hypervisor is %s" % hypervisor)
    logger.debug("the uri to connect is %s" % uri)

    if params.has_key('imagepath') and not params.has_key('volumepath'):
        imgfullpath = os.path.join(params.get('imagepath'), guestname)
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

    if params.has_key('imagetype'):
        imagetype = params.get('imagetype')
    else:
        imagetype = 'raw'

    logger.info("create disk image with size %sG, format %s" % (seeksize, imagetype))
    disk_create = "qemu-img create -f %s %s %sG" % \
                    (imagetype, imgfullpath, seeksize)
    logger.debug("the commands line of creating disk images is '%s'" % \
                   disk_create)

    (status, message) = commands.getstatusoutput(disk_create)

    if status != 0:
        logger.debug(message)
    else:
        logger.info("creating disk images file is successful.")

    logger.info("get system environment information")
    envfile = os.path.join(HOME_PATH, 'env.cfg')
    logger.info("the environment file is %s" % envfile)

    # Get iso file based on guest os and arch from env.cfg
    envparser = env_parser.Envparser(envfile)
    iso_file = envparser.get_value("guest", guestos + '_' + guestarch)
    cdkey = envparser.get_value("guest", "%s_%s_key" % (guestos, guestarch))

    windows_unattended_path = os.path.join(HOME_PATH,
                              "repos/domain/windows_unattended")

    logger.debug('install source: \n    %s' % iso_file)

    logger.info('prepare pre-installation environment...')
    logger.info('mount windows nfs server to /mnt/libvirt_windows')

    status, iso_local_path = prepare_iso(iso_file, ISO_MOUNT_POINT)
    if status:
        logger.error("installation failed")
        return 1
    params['bootcd'] = iso_local_path

    status = prepare_floppy_image(guestname, guestos, guestarch,
                                  windows_unattended_path, cdkey, FLOOPY_IMG)
    if status:
        logger.error("making floppy image failed")
        return 1
    params['floppysource'] = FLOOPY_IMG

    xmlobj = xmlbuilder.XmlBuilder()
    guestxml = xmlobj.build_domain_install_win(params)
    logger.debug('dump installation guest xml:\n%s' % guestxml)

    # Generate guest xml
    conn = libvirt.open(uri)
    installtype = params.get('type')
    if installtype == None or installtype == 'define':
        logger.info('define guest from xml description')
        try:
            domobj = conn.defineXML(guestxml)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to define domain %s" % guestname)
            return return_close(conn, logger, 1)

        logger.info('start installation guest ...')

        try:
            domobj.create()
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to start domain %s" % guestname)
            return return_close(conn, logger, 1)
    elif installtype == 'create':
        logger.info('create guest from xml description')
        try:
            conn.createXML(guestxml, 0)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to define domain %s" % guestname)
            return return_close(conn, logger, 1)

    interval = 0
    while(interval < 7200):
        time.sleep(20)
        if installtype == None or installtype == 'define':
            state = domobj.info()[0]
            if(state == libvirt.VIR_DOMAIN_SHUTOFF):
                logger.info("guest installaton of define type is complete.")
                logger.info("boot guest vm off harddisk")
                ret  = prepare_boot_guest(domobj, params, installtype)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return return_close(conn, logger, 1)
                break
            else:
                interval += 20
                logger.info('%s seconds passed away...' % interval)
        elif installtype == 'create':
            guest_names = []
            ids = conn.listDomainsID()
            for id in ids:
                obj = conn.lookupByID(id)
                guest_names.append(obj.name())

            if guestname not in guest_names:
                logger.info("guest installation of create type is complete.")
                logger.info("define the vm and boot it up")
                ret = prepare_boot_guest(domobj, params, installtype)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return return_close(conn, logger, 1)
                break
            else:
                interval += 20
                logger.info('%s seconds passed away...' % interval)

    if interval == 7200:
        logger.info("guest installation timeout 7200s")
        return return_close(conn, logger, 1)
    else:
        logger.info("guest is booting up")

    logger.info("get the mac address of vm %s" % guestname)
    mac = utils.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 600

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = utils.mac_to_ip(mac, 0)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % guestname)
            logger.info("the ip address of vm %s is %s" % (guestname, ip))

            break

    if timeout == 0:
        logger.info("fail to power on vm %s" % guestname)
        return return_close(conn, logger, 1)

    time.sleep(60)

    return return_close(conn, logger, 0)

def install_windows_cdrom_clean(params):
    """ clean testing environment """
    logger = params['logger']
    guestname = params.get('guestname')
    guesttype = params.get('guesttype')

    hypervisor = utils.get_hypervisor()
    if hypervisor == 'xen':
        imgfullpath = os.path.join('/var/lib/xen/images', guestname)
    elif hypervisor == 'kvm':
        imgfullpath = os.path.join('/var/lib/libvirt/images', guestname)

    (status, output) = commands.getstatusoutput(VIRSH_QUIET_LIST % guestname)
    if status:
        pass
    else:
        logger.info("remove guest %s, and its disk image file" % guestname)
        (status, output) = commands.getstatusoutput(VM_STAT % guestname)
        if status:
            (status, output) = commands.getstatusoutput(VM_DESTROY % guestname)
            if status:
                logger.error("failed to destroy guest %s" % guestname)
                logger.error("%s" % output)
            else:
                (status, output) = commands.getstatusoutput(VM_UNDEFINE % guestname)
                if status:
                    logger.error("failed to undefine guest %s" % guestname)
                    logger.error("%s" % output)
        else:
            (status, output) = commands.getstatusoutput(VM_UNDEFINE % guestname)
            if status:
                logger.error("failed to undefine guest %s" % guestname)
                logger.error("%s" % output)

    guestos = params.get('guestos')
    guestarch = params.get('guestarch')

    envfile = os.path.join(HOME_PATH, 'env.cfg')
    envparser = env_parser.Envparser(envfile)
    iso_file = envparser.get_value("guest", guestos + '_' + guestarch)

    status, iso_local_path = prepare_iso(iso_file, ISO_MOUNT_POINT)
    if os.path.exists(iso_local_path):
        os.remove(iso_local_path)

    iso_local_path_1 = iso_local_path + ".1"
    if os.path.exists(iso_local_path_1):
        os.remove(iso_local_path_1)

    if os.path.exists(imgfullpath):
        os.remove(imgfullpath)

    if os.path.exists(FLOOPY_IMG):
        os.remove(FLOOPY_IMG)
