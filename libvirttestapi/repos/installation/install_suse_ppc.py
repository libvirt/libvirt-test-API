# Install a linux domain from CDROM
# The iso file may be locked by other proces, and cause the failure of installation
import os
import re
import time
import shutil
import libvirt

from six.moves import urllib
from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.src import env_parser
from libvirttestapi.utils import utils, process
from libvirttestapi.repos.domain import domain_common

required_params = ('guestname', 'guestos', 'guestarch',)
optional_params = {
                   'memory': 2097152,
                   'vcpu': 1,
                   'disksize': 10,
                   'diskpath': '/var/lib/libvirt/images/libvirt-test-api',
                   'imageformat': 'raw',
                   'hddriver': 'virtio',
                   'nicdriver': 'virtio',
                   'macaddr': '52:54:00:97:e4:28',
                   'uuid': '05867c1a-afeb-300e-e55e-2673391ae080',
                   'type': 'define',
                   'xml': 'xmls/install_suse_ppc.xml',
                   'guestmachine': 'pseries',
                   'networksource': 'default',
                   'bridgename': 'virbr0',
                   'graphic': "vnc",
                   'disksymbol': 'sdb'
}

HOME_PATH = os.getcwd()


def cleanup(mount, logger):
    """Clean up a previously used mountpoint.
       @param mount: Mountpoint to be cleaned up.
    """
    if os.path.isdir(mount):
        if os.path.ismount(mount):
            logger.info("Path %s is still mounted, please verify" % mount)
            cmd = "umount -l  %s" % mount
            ret = process.run(cmd, shell=True, ignore_status=True)
            logger.info("the floppy mount point folder exists, remove it")
            shutil.rmtree(mount)
        else:
            logger.info("Removing mount point %s" % mount)
            os.rmdir(mount)
    os.makedirs(mount)
    logger.info("making the directory %s" % mount)


def prepare_ks(ks, guestos, hddriver, ks_path, logger):
    """Prepare the ks file for suse installation
       virtio bus use the vda instead of sda in ide or scsi bus
    """
    urllib.request.urlretrieve(ks, ks_path)
    logger.info("the url of kickstart is %s" % ks)
    if (hddriver == "virtio" or hddriver == "lun") and "suse" in guestos:
        with open(ks_path, "r+") as f:
            ks_content = f.read()
            f.close()
        ks_content = ks_content.replace("sda", 'vda')
        with open(ks_path, "w+") as f:
            f.write(ks_content)
            f.close()


def prepare_floppy(ks_path, mount_point, floppy_path, logger):
    """ Prepare a floppy containing autoinst.xml
    """
    if os.path.exists(floppy_path):
        os.remove(floppy_path)
    cmd = 'dd if=/dev/zero of=%s bs=1440k count=1' % floppy_path
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error("failed to create floppy image")
        return 1
    cmd = 'mkfs.msdos -s 1 %s' % floppy_path
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error("failed to format floppy image")
        return 1
    if os.path.exists(mount_point):
        logger.info("the floppy mount point folder exists, remove it")
        cmd = "umount -l %s" % mount_point
        ret = process.run(cmd, shell=True, ignore_status=True)
        shutil.rmtree(mount_point)
    logger.info("create mount point %s" % mount_point)
    os.makedirs(mount_point)
    cmd = 'mount -o loop %s %s' % (floppy_path, mount_point)
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error(
            "failed to mount /tmp/floppy.img to /mnt/libvirt_floppy")
        return 1
    shutil.copy(ks_path, mount_point)
    return 0


def prepare_cdrom(ostree, ks, guestname, guestos, guestarch, hddriver, cache_folder, logger):
    """ to customize boot.iso file to add kickstart
        file into it for automatic guest installation
    """
    new_dir = cache_folder + "/" + ostree.split("/")[-1].split(".iso")[0]

    # prepare the cache_folder
    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)
        logger.info("making directory %s" % cache_folder)

    if os.path.exists(new_dir):
        logger.info("the folder exists, remove it")
        shutil.rmtree(new_dir)
    os.makedirs(new_dir)
    os.makedirs(new_dir + "/custom")
    logger.info("creating working folder for customizing custom.iso file")

    # mount point is /mnt/custom
    mount_point = "/mnt/custom"
    cleanup(mount_point, logger)
    iso_path = new_dir + "/" + ostree.split("/")[-1]
    logger.info("Downloading the iso file")
    cmd = "wget " + ostree + " -P " + new_dir
    utils.exec_cmd(cmd, shell=True)

    # copy iso file
    cmd = "mount -o loop %s %s" % (iso_path, mount_point)
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error("mount iso failure")
        return 1

    if "suse" in guestos and "ppc" in guestarch:
        if 'ppc64le' in guestarch:
            shutil.copy(mount_point + '/boot/ppc64le/linux', '/var/lib/libvirt/boot/')
            shutil.copy(mount_point + '/boot/ppc64le/initrd', '/var/lib/libvirt/boot/')
        elif 'ppc64' in guestarch:
            shutil.copy(mount_point + '/suseboot/linux64', '/var/lib/libvirt/boot/')
            shutil.copy(mount_point + '/suseboot/initrd64', '/var/lib/libvirt/boot/')

        cmd = "umount -l %s" % mount_point
        ret = process.run(cmd, shell=True, ignore_status=True)
        if ret.exit_status:
            logger.error("unmount iso failure: %s " % ret.stdout)
            return 1

        shutil.move(iso_path, new_dir + '/custom.iso')
        return new_dir

    logger.info("Copying the iso file to working directory")
    cmd = "cp -rf %s/* %s/custom" % (mount_point, new_dir)
    ret = process.run(cmd, shell=True, ignore_status=True)

    # prepare the custom iso
    if "ubuntu" in guestos:
        cmd = cmd = "cp -rf %s/.disk %s/custom" % (mount_point, new_dir)
        ret = process.run(cmd, shell=True, ignore_status=True)
        prepare_ks(ks, guestos, hddriver, new_dir + "/custom/install/ks.cfg", logger)
        os.remove(new_dir + "/custom/isolinux/isolinux.cfg")
        shutil.copy(HOME_PATH + "/repos/installation/isolinux/ubuntu/isolinux.cfg",
                    new_dir + "/custom/isolinux/")
        MAKE_ISO = "mkisofs -o %s/custom.iso -J -r -v -R -b \
                    isolinux/isolinux.bin -c isolinux/boot.cat \
                    -no-emul-boot -boot-load-size 4 \
                    -boot-info-table %s"
        logger.info("Making the custom.iso file")
        cmd = MAKE_ISO % (new_dir, new_dir + "/custom")
        ret = process.run(cmd, shell=True, ignore_status=True)
    if "ppc" not in guestarch:
        prepare_ks(ks, guestos, hddriver, new_dir + "/custom/autoinst.xml", logger)
        flag = prepare_floppy(new_dir + "/custom/autoinst.xml",
                              "/mnt/floppy",
                              new_dir + "/floppy.img", logger)
        if flag == 1:
            logger.info("Create floppy file failing")
            return 1

        isolinux_location = new_dir + "/custom/boot/" + guestarch + "/loader/"
        os.remove(isolinux_location + "isolinux.cfg")
        shutil.copy(HOME_PATH + "/repos/installation/isolinux/suse/isolinux.cfg",
                    isolinux_location)
        logger.info("Making the custom.iso file")
        if guestarch == "i386":
            MAKE_ISO = 'mkisofs -o %s/custom.iso -J -r -v -R -b \
                        boot/i386/loader/isolinux.bin -c boot.cat \
                        -no-emul-boot -boot-load-size 4 \
                        -boot-info-table %s'
            cmd = MAKE_ISO % (new_dir, new_dir + "/custom")
            ret = process.run(cmd, shell=True, ignore_status=True)
        else:
            MAKE_ISO = 'mkisofs -o %s/custom.iso -J -r -v -R -b \
                        boot/x86_64/loader/isolinux.bin -c boot.cat \
                        -no-emul-boot -boot-load-size 4 \
                        -boot-info-table %s'
            cmd = MAKE_ISO % (new_dir, new_dir + "/custom")
            ret = process.run(cmd, shell=True, ignore_status=True)

    if ret.exit_status:
        logger.error(ret.stdout)
        logger.error("makeing iso failure")
        return 1

    os.remove(iso_path)
    cmd = "umount -l /mnt/floppy"
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error("failed to umount %s" % mount_point)

    cmd = "umount -l %s" % mount_point
    ret = process.run(cmd, shell=True, ignore_status=True)
    return new_dir


def prepare_boot_guest(domobj, xmlstr, guestname, installtype, logger):
    """ After guest installation is over, undefine the guest with
        bootting off cdrom, to define the guest to boot off harddisk.
    """
    xmlstr = re.sub("<disk type='file' device='floppy'>.*\n.*\n.*\n.*\n.*\n    ", '', xmlstr)
    xmlstr = xmlstr.replace("<boot dev='cdrom'/>", '<boot dev="hd"/>')
    xmlstr = re.sub("<disk type='file' device='cdrom'>.*\n.*\n.*\n.*\n.*\n    ", '', xmlstr)
    xmlstr = re.sub("<kernel>.*</kernel>", '', xmlstr)
    xmlstr = re.sub("<initrd>.*</initrd>", '', xmlstr)
    xmlstr = re.sub("<cmdline>.*</cmdline>", '', xmlstr)

    if installtype != 'create':
        domobj.undefine()
        logger.info("undefine %s : \n" % guestname)

    try:
        conn = domobj._conn
        domobj = conn.defineXML(xmlstr)
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        logger.error("fail to define domain %s" % guestname)
        return 1

    logger.info("define guest %s " % guestname)
    logger.debug("the xml description of guest booting off harddisk is %s" %
                 xmlstr)

    logger.info('boot guest up ...')

    try:
        domobj.create()
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        logger.error("fail to start domain %s" % guestname)
        return 1

    return 0


def check_domain_state(conn, guestname, logger):
    """ if a guest with the same name exists, remove it """
    running_guests = []
    ids = conn.listDomainsID()
    for id in ids:
        obj = conn.lookupByID(id)
        running_guests.append(obj.name())

    if guestname in running_guests:
        logger.info("A guest with the same name %s is running!" % guestname)
        logger.info("destroy it...")
        domobj = conn.lookupByName(guestname)
        domobj.destroy()

    defined_guests = conn.listDefinedDomains()

    if guestname in defined_guests:
        logger.info("undefine the guest with the same name %s" % guestname)
        domobj = conn.lookupByName(guestname)
        domobj.undefine()

    return 0


def install_suse_ppc(params):
    """ install a new virtual machine """

    xmlstr = params['xml']
    logger = params['logger']

    guestname = params.get('guestname')
    guestos = params.get('guestos')
    guestarch = params.get('guestarch')
    br = params.get('bridgename', 'virbr0')
    nicdriver = params.get('nicdriver', 'virtio')
    hddriver = params.get('hddriver', 'virtio')
    diskpath = params.get('diskpath', '/var/lib/libvirt/images/libvirt-test-api')
    seeksize = params.get('disksize', 20)
    imageformat = params.get('imageformat', 'qcow2')
    graphic = params.get('graphic', 'vnc')
    video = params.get('video', 'qxl')
    installtype = params.get('type', 'define')

    logger.info("guestname: %s" % guestname)
    params_info = "%s, %s, " % (guestos, guestarch)
    params_info += "%s(network), %s(disk), " % (nicdriver, hddriver)
    params_info += "%s, %s, " % (imageformat, graphic)
    params_info += "%s, %s(storage)" % (video, 'local')
    logger.info("%s" % params_info)

    conn = sharedmod.libvirtobj['conn']
    check_domain_state(conn, guestname, logger)

    if 'ppc' not in guestarch:
        tmpdiskpath = diskpath
        if not os.path.exists(tmpdiskpath):
            os.mkdir(tmpdiskpath)
        diskpath = diskpath + '/' + guestname
        xmlstr = xmlstr.replace(tmpdiskpath, diskpath)

    # prepare the image
    logger.info("disk image is %s" % diskpath)
    if hddriver != 'lun' and hddriver != "scsilun":
        disk_create = "qemu-img create -f %s %s %sG" % \
            (imageformat, diskpath, seeksize)
        logger.debug("the command line of creating disk images is '%s'" %
                     disk_create)
        ret = process.run(disk_create, shell=True, ignore_status=True)
        if ret.exit_status != 0:
            logger.debug(ret.stdout)
            return 1
        os.chown(diskpath, 107, 107)
        logger.info("creating disk images file is successful.")

    if hddriver == 'virtio':
        xmlstr = xmlstr.replace('DEV', 'vda')
    elif hddriver == 'ide':
        xmlstr = xmlstr.replace('DEV', 'hda')
    elif hddriver == 'scsi':
        xmlstr = xmlstr.replace('DEV', 'sda')
    elif hddriver == "sata":
        xmlstr = xmlstr.replace("DEV", 'sda')
    elif hddriver == 'lun':
        xmlstr = xmlstr.replace("'lun'", "'virtio'")
        xmlstr = xmlstr.replace('DEV', 'vda')
        xmlstr = xmlstr.replace("'file'", "'block'")
        xmlstr = xmlstr.replace("'disk'", "'lun'")
        tmp = params.get('diskpath', '/var/lib/libvirt/images') + '/' + guestname
        xmlstr = xmlstr.replace("file='%s'" % tmp,
                                "dev='/dev/SDX'")
        disksymbol = params.get('disksymbol', 'sdb')
        xmlstr = xmlstr.replace('SDX', disksymbol)
        xmlstr = xmlstr.replace("<disk type='block' device='cdrom'>",
                                "<disk type='file' device='cdrom'>")
    elif hddriver == 'scsilun':
        xmlstr = xmlstr.replace("'scsilun'", "'scsi'")
        xmlstr = xmlstr.replace('DEV', 'sda')
        xmlstr = xmlstr.replace("'file'", "'block'")
        xmlstr = xmlstr.replace("'disk'", "'lun'")
        tmp = params.get('diskpath', '/var/lib/libvirt/images') + '/' + guestname
        xmlstr = xmlstr.replace("file='%s'" % tmp,
                                "dev='/dev/SDX'")
        disksymbol = params.get('disksymbol', 'sdb')
        xmlstr = xmlstr.replace('SDX', disksymbol)
        xmlstr = xmlstr.replace("<disk type='block' device='cdrom'>",
                                "<disk type='file' device='cdrom'>")

    # prepare the custom iso
    logger.info("get system environment information")
    envfile = os.path.join(HOME_PATH, 'global.cfg')
    logger.info("the environment file is %s" % envfile)

    os_arch = guestos + "_" + guestarch

    envparser = env_parser.Envparser(envfile)
    ostree = envparser.get_value("guest", os_arch + "_iso")
    ks = envparser.get_value("guest", os_arch + "_iso_ks")

    xmlstr = xmlstr.replace('AUTOYAST', ks)

    if 'ppc64le' in guestarch:
        xmlstr = xmlstr.replace('KERNEL', '/var/lib/libvirt/boot/linux')
        xmlstr = xmlstr.replace('INITRD', '/var/lib/libvirt/boot/initrd')
    elif 'ppc' in guestarch:
        xmlstr = xmlstr.replace('KERNEL', '/var/lib/libvirt/boot/linux64')
        xmlstr = xmlstr.replace('INITRD', '/var/lib/libvirt/boot/initrd64')

    logger.debug('install source:\n    %s' % ostree)
    logger.debug('kisckstart file:\n    %s' % ks)

    if (ostree == 'http://'):
        logger.error("no os tree defined in %s for %s" % (envfile, os_arch))
        return 1

    logger.info('prepare installation...')
    cache_folder = envparser.get_value("variables", "domain_cache_folder")

    logger.info("begin to customize the custom.iso file")
    custom = prepare_cdrom(ostree, ks, guestname, guestos, guestarch, hddriver, cache_folder, logger)
    xmlstr = xmlstr.replace("<disk type='block' device='floppy'>\n",
                            "<disk type='file' device='floppy'>\n")
    if "suse" in guestos:
        xmlstr = xmlstr.replace("FLOPPY", custom + "/floppy.img")
    else:
        xmlstr = re.sub("<disk type='file' device='floppy'>.*\n.*\n.*\n.*\n.*\n    ", '', xmlstr)

    if custom == 1:
        logger.error("fail to prepare custom iso")
        return 1
    else:
        bootcd = custom + "/custom.iso"
    xmlstr = xmlstr.replace('CUSTOMISO', bootcd)
    logger.debug('dump installation guest xml:\n%s' % xmlstr)
    if installtype == 'define':
        logger.info('define guest from xml description')
        try:
            domobj = conn.defineXML(xmlstr)
        except libvirtError as e:
            logger.error("API error message: %s, error code is %s"
                         % (e.get_error_message(), e.get_error_code()))
            logger.error("fail to define domain %s" % guestname)
            return 1

        logger.info('start installation guest ...')

        try:
            domobj.create()
        except libvirtError as e:
            logger.error("API error message: %s, error code is %s"
                         % (e.get_error_message(), e.get_error_code()))
            logger.error("fail to start domain %s" % guestname)
            return 1
    elif installtype == 'create':
        logger.info('create guest from xml description')
        try:
            domobj = conn.createXML(xmlstr, 0)
        except libvirtError as e:
            logger.error("API error message: %s, error code is %s"
                         % (e.get_error_message(), e.get_error_code()))
            logger.error("fail to define domain %s" % guestname)
            return 1

    interval = 0
    while(interval < 2400):
        time.sleep(10)
        if installtype == 'define':
            try:
                state = domobj.info()[0]
            except libvirtError as e:
                logger.error("API error message: %s, error code is %s"
                             % (e.get_error_message(), e.get_error_code()))
                return 1
            if(state == libvirt.VIR_DOMAIN_SHUTOFF):
                logger.info("guest installaton of define type is complete.")
                logger.info("boot guest vm off harddisk")
                ret = prepare_boot_guest(domobj, xmlstr, guestname, installtype, logger)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return 1
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
                logger.info("guest installation of create type is complete.")
                logger.info("define the vm and boot it up")
                ret = prepare_boot_guest(domobj, xmlstr, guestname, installtype, logger)
                if ret:
                    logger.info("booting guest vm off harddisk failed")
                    return 1
                break
            else:
                interval += 10
                logger.info('%s seconds passed away...' % interval)

    logger.info("guest is booting up")

    logger.info("get the mac address of vm %s" % guestname)
    mac = utils.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 300

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = utils.mac_to_ip(mac, 180, br)

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


def install_suse_ppc_clean(params):
    """ clean testing environment """
    logger = params['logger']
    guestname = params.get('guestname')

    diskpath = params.get('diskpath', '/var/lib/libvirt/images/libvirt-test-api')
    conn = libvirt.open()
    domain_common.guest_clean(conn, guestname, logger)

    if os.path.exists(diskpath + '/' + guestname):
        os.remove(diskpath + '/' + guestname)

    envfile = os.path.join(HOME_PATH, 'global.cfg')
    envparser = env_parser.Envparser(envfile)
    ostree_search = params.get('guestos') + "_" + params.get('guestarch') + "_iso"
    ostree = envparser.get_value("guest", ostree_search)
    cache_folder = envparser.get_value("variables", "domain_cache_folder") + "/" +\
        ostree.split("/")[-1].split(".iso")[0]
    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)

    guest_dir = os.path.join(HOME_PATH, guestname)
    if os.path.exists(guest_dir):
        shutil.rmtree(guest_dir)
