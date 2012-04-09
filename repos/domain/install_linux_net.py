#! /usr/bin/env python
# Install a linux domain from network

import os
import sys
import re
import time
import copy
import commands
import shutil
import urllib

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import env_parser
from utils import xmlbuilder

VIRSH_QUIET_LIST = "virsh --quiet list --all|awk '{print $2}'|grep \"^%s$\""
VM_STAT = "virsh --quiet list --all| grep \"\\b%s\\b\"|grep off"
VM_DESTROY = "virsh destroy %s"
VM_UNDEFINE = "virsh undefine %s"

BOOT_DIR = "/var/lib/libvirt/boot/"
HOME_PATH = os.getcwd()

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Checking the arguments required"""
    params_given = copy.deepcopy(params)

    mandatory_args = ['guestname', 'guesttype', 'guestos',
                      'guestarch','netmethod']

    optional_args = ['uuid', 'memory', 'vcpu', 'disksize',
                     'imagepath', 'hdmodel', 'nicmodel',
                     'ifacetype', 'imagetype', 'source',
                     'type']

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

def prepare_boot_guest(domobj, dict, logger, installtype):
    """After guest installation is over, undefine the guest with
       bootting off cdrom, to define the guest to boot off harddisk.
    """
    params = copy.deepcopy(dict)

    if params.has_key('kickstart'):
        params.pop('kickstart')

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

def prepare_cdrom(*args):
    """ to customize boot.iso file to add kickstart
        file into it for automatic guest installation
    """
    ostree, ks, guestname, logger = args
    ks_name = os.path.basename(ks)

    new_dir = os.path.join(HOME_PATH, guestname)
    logger.info("creating a new folder for customizing custom.iso file in it")

    if os.path.exists(new_dir):
        logger.info("the folder exists, remove it")
        shutils.rmtree(new_dir)

    os.makedirs(new_dir)
    logger.info("the directory is %s" % new_dir)

    boot_path = os.path.join(ostree, 'images/boot.iso')
    logger.info("the url of downloading boot.iso file is %s" % boot_path)

    urllib.urlretrieve(boot_path, '%s/boot.iso' % new_dir)[0]
    time.sleep(10)

    urllib.urlretrieve(ks, '%s/%s' % (new_dir, ks_name))[0]
    logger.info("the url of kickstart is %s" % ks)

    shutils.copy('utils/ksiso.sh', new_dir)
    src_path = os.getcwd()

    logger.info("enter into the workshop folder: %s" % new_dir)
    os.chdir(new_dir)
    shell_cmd = 'sh ksiso.sh %s' % ks_name

    logger.info("running command %s to making the custom.iso file" % shell_cmd)
    (status, text) = commands.getstatusoutput(shell_cmd)

    logger.debug(text)
    logger.info("make custom.iso file, change to original directory: %s" %
                src_path)
    os.chdir(src_path)

def install_linux_net(params):
    """install a new virtual machine"""
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
    installmethod = params.get('netmethod')

    logger.info("the name of guest is %s" % guestname)
    logger.info("the type of guest is %s" % guesttype)
    logger.info("the installation method is %s" % installmethod)

    hypervisor = utils.get_hypervisor()
    macaddr = utils.get_rand_mac()

    logger.info("the macaddress is %s" % macaddr)
    logger.info("the type of hypervisor is %s" % hypervisor)
    logger.debug("the uri to connect is %s" % uri)

    if params.has_key('imagepath'):
        fullimagepath = os.path.join(params.get('imagepath'), guestname)
    else:
        if hypervisor == 'xen':
            fullimagepath = os.path.join('/var/lib/xen/images', guestname)
        elif hypervisor == 'kvm':
            fullimagepath = os.path.join('/var/lib/libvirt/images', guestname)

    params['fullimagepath'] = fullimagepath

    logger.info("the path of directory of disk images located on is %s" %
                fullimagepath)

    if params.has_key('disksize'):
        seeksize = params.get('disksize')
    else:
        seeksize = '10'

    if params.has_key('imagetype'):
        imagetype = params.get('imagetype')
    else:
        imagetype = 'raw'

    logger.info("create disk image with size %sG, format %s" % (seeksize, imagetype))
    disk_create = "qemu-img create -f %s %s %sG" % \
                    (imagetype, fullimagepath, seeksize)
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

    envparser = env_parser.Envparser(envfile)

    # Get http, ftp or nfs url based on guest os, arch
    # and installation method from env.cfg

    if installmethod == 'http':
        ks = envparser.get_value("guest", guestos + "_" + guestarch +
                                "_http_ks")
    elif installmethod == 'ftp':
        ks = envparser.get_value("guest", guestos + "_" + guestarch + "_ftp_ks")
    elif installmethod == "nfs":
        ks = envparser.get_value("guest", guestos + "_" + guestarch + "_nfs_ks")

    ostree = envparser.get_value("guest", guestos + "_" + guestarch)

    logger.debug('install source: \n    %s' % ostree)
    logger.debug('kisckstart file: \n    %s' % ks)

    logger.info('prepare installation...')

    if guesttype == 'xenpv' or guesttype == 'kvm':
        params['kickstart'] = ks
        params['macaddr'] = macaddr

        if guesttype == 'kvm':
            vmlinuzpath = os.path.join(ostree, 'isolinux/vmlinuz')
            initrdpath = os.path.join(ostree, 'isolinux/initrd.img')
        else:
            vmlinuzpath = os.path.join(ostree, 'images/xen/vmlinuz')
            initrdpath = os.path.join(ostree, 'images/xen/initrd.img')

        logger.debug("the url of vmlinuz file is %s" % vmlinuzpath)
        logger.debug("the url of initrd file is %s" % initrdpath)

        urllib.urlretrieve(vmlinuzpath, '/var/lib/libvirt/boot/vmlinuz')
        urllib.urlretrieve(initrdpath, '/var/lib/libvirt/boot/initrd.img')

        logger.debug("vmlinuz file is located in /var/lib/libvirt/boot")
        logger.debug("initrd file is located in /var/lib/libvirt/boot")
    elif guesttype == 'xenfv':
        params['bootcd'] = '%s/custom.iso' % \
                           (os.path.join(HOME_PATH, guestname))
        logger.debug("the bootcd path is %s" % params['bootcd'])
        logger.info("begin to customize the custom.iso file")
        prepare_cdrom(ostree, ks, guestname, logger)
    else:
        logger.error("unknown guest type %s" % guesttype)

    # Prepare guest installation xml
    xmlobj = xmlbuilder.XmlBuilder()
    guestxml = xmlobj.build_domain_install(params)
    logger.debug('dump installation guest xml:\n%s' % guestxml)

    #start installation
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
            domobj = conn.createXML(guestxml, 0)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to define domain %s" % guestname)
            return return_close(conn, logger, 1)

    if 'rhel3u9' in guestos:
        interval = 0
        logger.info("waiting 1000 seconds for the installation to complete...")
        while(interval < 1000):
            logger.info('%s seconds passed away...' % interval)
            time.sleep(10)
            interval += 10

        domobj.destroy()
        ret =  prepare_boot_guest(domobj, params, logger, installtype)

        if ret:
            logger.info("booting guest vm off harddisk failed")
            return return_close(conn, logger, 1)
        else:
            logger.info("geust is booting up")
    else:
        interval = 0
        while(interval < 3600):
            time.sleep(10)
            if installtype == None or installtype == 'define':
                state = domobj.info()[0]
                if(state == libvirt.VIR_DOMAIN_SHUTOFF):
                    logger.info("guest installaton of define type is complete")
                    logger.info("boot guest vm off harddisk")
                    ret  = prepare_boot_guest(domobj, params, logger, \
                                              installtype)
                    if ret:
                        logger.info("booting guest vm off harddisk failed")
                        return return_close(conn, logger, 1)
                    break
                else:
                    interval += 10
                    logger.info('%s seconds passed away...' % interval)
            elif installtype == 'create':
                guest_names = []
                ids = conn.listDomainsID()
                for id in ids:
                    obj = conn.lookupByID(id)
                    guest_names.append(obj.name())

                if guestname not in guest_names:
                    logger.info("guest installation of create type is complete")
                    logger.info("define the vm and boot it up")
                    ret = prepare_boot_guest(domobj, params, logger, \
                                             installtype)
                    if ret:
                        logger.info("booting guest vm off harddisk failed")
                        return return_close(conn, logger, 1)
                    break
                else:
                    interval += 10
                    logger.info('%s seconds passed away...' % interval)

        if interval == 3600:
            logger.info("guest installation timeout 3600s")
            return return_close(conn, logger, 1)
        else:
            logger.info("guest is booting up")

    logger.info("get the mac address of vm %s" % guestname)
    mac = utils.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 300
    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = utils.mac_to_ip(mac, 180)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % guestname)
            logger.info("the ip address of vm %s is %s" % (guestname, ip))
            break

        if timeout == 0:
            logger.info("fail to power on vm %s" % guestname)
            return return_close(conn, logger, 1)

    return return_close(conn, logger, 0)

def install_linux_net_clean(params):
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

    if os.path.exists(imgfullpath):
        os.remove(imgfullpath)

    if guesttype == 'xenpv' or guesttype == 'kvm':
        vmlinuz = os.path.join(BOOT_DIR, 'vmlinuz')
        initrd = os.path.join(BOOT_DIR, 'initrd.img')
        if os.path.exists(vmlinuz):
            os.remove(vmlinuz)
        if os.path.exists(initrd):
            os.remove(initrd)
    elif guesttype == 'xenfv':
        guest_dir = os.path.join(HOME_PATH, guestname)
        if os.path.exists(guest_dir):
            shutils.rmtree(guest_dir)
