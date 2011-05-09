#!/usr/bin/env python
"""The test script is for installing a new guest virtual machine
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
import urllib

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

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils
from utils.Python import env_parser
from utils.Python import xmlbuilder
from exception import LibvirtAPI

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Mar 11 2010"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2010 Red Hat, Inc."
__all__ = ['install_linux_cdrom', 'usage']

VIRSH_QUIET_LIST = "virsh --quiet list --all|awk '{print $2}'|grep \"^%s$\""
VM_STAT = "virsh --quiet list --all| grep \"\\b%s\\b\"|grep off"
VM_DESTROY = "virsh destroy %s"
VM_UNDEFINE = "virsh undefine %s"

BOOT_DIR = "/var/lib/libvirt/boot/"

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def usage():
    print '''usage: mandatory arguments:guesttype
                           guestname
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

def prepare_cdrom(*args):
    """ to customize boot.iso file to add kickstart
        file into it for automatic guest installation
    """
    ostree, ks, guestname, logger = args
    ks_name = os.path.basename(ks)

    new_dir = os.path.join(homepath, guestname)
    logger.info("creating a new folder for customizing custom.iso file in it")

    if os.path.exists(new_dir):
        logger.info("the folder exists, remove it")
        shutil.rmtree(new_dir)

    os.makedirs(new_dir)
    logger.info("the directory is %s" % new_dir)

    boot_path = os.path.join(ostree, 'images/boot.iso')
    logger.info("the url of downloading boot.iso file is %s" % boot_path)

    urllib.urlretrieve(boot_path, '%s/boot.iso' % new_dir)[0]
    time.sleep(10)

    urllib.urlretrieve(ks, '%s/%s' % (new_dir, ks_name))[0]
    logger.info("the url of kickstart is %s" % ks)

    shutil.copy('utils/ksiso.sh', new_dir)
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

def prepare_boot_guest(domobj, dict, logger, installtype):
    """ After guest installation is over, undefine the guest with
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

def check_domain_state(domobj, guestname, logger):
    """ if a guest with the same name exists, remove it """
    running_guests = domobj.get_list()

    if guestname in running_guests:
        logger.info("A guest with the same name %s is running!" % guestname)
        logger.info("destroy it...")
        domobj.destroy(guestname)

    defined_guests = domobj.get_defined_list()

    if guestname in defined_guests:
        logger.info("undefine the guest with the same name %s" % guestname)
        domobj.undefine(guestname)

    return 0

def install_linux_cdrom(params):
    """ install a new virtual machine """
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
    uri = util.get_uri('127.0.0.1')
    hypervisor = util.get_hypervisor()
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)

    check_domain_state(domobj, guestname, logger)

    if not params.has_key('macaddr'):
        macaddr = util.get_rand_mac()
        params['macaddr'] = macaddr

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
        logger.error("we only choose one between imagepath and volumepath")
        return return_close(conn, logger, 1)

    params['fullimagepath'] = imgfullpath

    logger.info("the path of directory of disk images located on is %s" %
                imgfullpath)

    if params.has_key('disksize'):
        seeksize = params.get('disksize')
    else:
        seeksize = '10'

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

    envparser = env_parser.Envparser(envfile)
    ostree = envparser.get_value("guest", guestos + "_" +guestarch)
    ks = envparser.get_value("guest", guestos + "_" +guestarch + "_http_ks")

    logger.debug('install source: \n    %s' % ostree)
    logger.debug('kisckstart file: \n    %s' % ks)

    logger.info('prepare installation...')

    if guesttype == 'xenpv':
        params['kickstart'] = ks
        vmlinuzpath = os.path.join(ostree, 'isolinux/vmlinuz')
        initrdpath = os.path.join(ostree, 'isolinux/initrd.img')

        logger.debug("the url of vmlinuz file is %s" % vmlinuzpath)
        logger.debug("the url of initrd file is %s" % initrdpath)

        urllib.urlretrieve(vmlinuzpath, os.path.join(BOOT_DIR, 'vmlinuz'))
        urllib.urlretrieve(initrdpath, os.path.join(BOOT_DIR, 'initrd.img'))

        logger.debug("vmlinuz and initrd.img is located in %s" % BOOT_DIR)

    elif guesttype == 'xenfv' or guesttype == 'kvm':
        params['bootcd'] = '%s/custom.iso' % \
                           (os.path.join(homepath, guestname))
        logger.debug("the bootcd path is %s" % params['bootcd'])
        logger.info("begin to customize the custom.iso file")
        prepare_cdrom(ostree, ks, guestname, logger)
    else:
        logger.error("unknown guest type: %s" % guesttype)
        return return_close(conn, logger, 1)

    xmlobj = xmlbuilder.XmlBuilder()
    guestxml = xmlobj.build_domain_install(params)
    logger.debug('dump installation guest xml:\n%s' % guestxml)

    installtype = params.get('type')

    if installtype == None or installtype == 'define':
        logger.info('define guest from xml description')
        try:
            domobj.define(guestxml)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" %
                         (e.response()['message'], e.response()['code']))
            logger.error("fail to define domain %s" % guestname)
            return return_close(conn, logger, 1)

        logger.info('start installation guest ...')

        try:
            domobj.start(guestname)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" %
                         (e.response()['message'], e.response()['code']))
            logger.error("fail to start domain %s" % guestname)
            return return_close(conn, logger, 1)
    elif installtype == 'create':
        logger.info('create guest from xml description')
        try:
            domobj.create(guestxml)
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" %
                         (e.response()['message'], e.response()['code']))
            logger.error("fail to define domain %s" % guestname)
            return return_close(conn, logger, 1)

    interval = 0
    while(interval < 2400):
        time.sleep(10)
        if installtype == None or installtype == 'define':
            state = domobj.get_state(guestname)
            if(state == "shutoff"):
                logger.info("guest installaton of define type is complete.")
                logger.info("boot guest vm off harddisk")
                ret  = prepare_boot_guest(domobj, params, logger, installtype)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return return_close(conn, logger, 1)
                break
            else:
                interval += 10
                logger.info('%s seconds passed away...' % interval)
        elif installtype == 'create':
            dom_name_list = domobj.get_list()
            if guestname not in dom_name_list:
                logger.info("guest installation of create type is complete.")
                logger.info("define the vm and boot it up")
                ret = prepare_boot_guest(domobj, params, logger, installtype)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return return_close(conn, logger, 1)
                break
            else:
                interval += 10
                logger.info('%s seconds passed away...' % interval)

    if interval == 2400:
        if 'rhel3u9' in guestname:
            logger.info(
            "guest installaton will be destoryed forcelly for rhel3u9 guest")
            domobj.destroy(guestname)
            logger.info("boot guest vm off harddisk")
            ret =  prepare_boot_guest(domobj, params, logger, installtype)
            if ret:
                logger.info("booting guest vm off harddisk failed")
                return return_close(conn, logger, 1)
        else:
            logger.info("guest installation timeout 2400s")
            return return_close(conn, logger, 1)
    else:
        logger.info("guest is booting up")

    logger.info("get the mac address of vm %s" % guestname)
    mac = util.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 300

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
        return return_close(conn, logger, 1)

    time.sleep(60)

    return return_close(conn, logger, 0)

def install_linux_cdrom_clean(params):
    """ clean testing environment """
    logger = params['logger']
    guestname = params.get('guestname')
    guesttype = params.get('guesttype')

    util = utils.Utils()
    hypervisor = util.get_hypervisor()
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

    if guesttype == 'xenpv':
        vmlinuz = os.path.join(BOOT_DIR, 'vmlinuz')
        initrd = os.path.join(BOOT_DIR, 'initrd.img')
        if os.path.exists(vmlinuz):
            os.remove(vmlinuz)
        if os.path.exists(initrd):
            os.remove(initrd)
    elif guesttype == 'xenfv' or guesttype == 'kvm':
        guest_dir = os.path.join(homepath, guestname)
        if os.path.exists(guest_dir):
            shutil.rmtree(guest_dir)
