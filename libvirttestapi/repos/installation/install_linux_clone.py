# Install a linux domain from CDROM
# The iso file may be locked by other proces, and cause the failure of installation
import os
import re
import time
import libvirt
import shutil
from libvirttestapi.src.exception import TestError

from libvirttestapi.src import sharedmod
from libvirttestapi.src.testcasexml import populate_xml_file
from libvirttestapi.utils import process, utils
from libvirttestapi.repos.installation import install_linux_bootiso, install_common
from libvirttestapi.repos.domain import start, destroy, undefine
from six.moves import urllib


required_params = ('guestname', 'guestos', 'guestarch',)
optional_params = {
                   'memory': 4194304,
                   'vcpu': 2,
                   'disksize': 14,
                   'diskpath': '/var/lib/libvirt/images/libvirt-test-api',
                   'imageformat': 'qcow2',
                   'hddriver': 'virtio',
                   'nicdriver': 'virtio',
                   'macaddr': '52:54:00:97:e4:28',
                   'uuid': '05867c1a-afeb-300e-e55e-2673391ae017',
                   'type': 'define',
                   'xml': 'xmls/kvm_linux_guest_install_cdrom.xml',
                   'guestmachine': 'pc',
                   'networksource': 'default',
                   'bridgename': 'virbr0',
                   'graphic': "spice",
                   'video': 'qxl',
                   'disksymbol': 'sdb',
                   'rhelnewest': '',
}



# this function will save plenty of test time
def install_linux_clone(params):
    logger = params['logger']
    guestname = params.get('guestname')
    guestos = params.get('guestos')
    guestarch = params.get('guestarch')
    diskpath = params.get('diskpath', '/var/lib/libvirt/images/libvirt-test-api')
    if utils.Is_Fedora():
        guestos = utils.get_value_from_global("variables", "fedoraos")
    diskpath_backup = "/var/lib/libvirt/images/lta_%s_%s" % (guestos, guestarch)
    guestname_backup = "lta_%s_%s" % (guestos, guestarch)
    # create a backup disk image if it is not present on the test machine
    if not os.path.exists(diskpath_backup):
        params['diskpath'] = diskpath_backup
        params['guestname'] = guestname_backup
        base_path = utils.get_base_path()
        xml_file = os.path.join(base_path, 'usr/share/libvirt-test-api/xmls', 'installation/kvm_clone.xml')
        params['xml'] = 'xmls/kvm_clone.xml'
        populate_xml_file(xml_file, params, optional_params)
        ret = install_linux_bootiso.install_linux_bootiso(params)
        if ret:
            logger.error("Failed to create the backup VM")
            return 1
        destroy.destroy(params)
    else:
        check_status = ('virsh list|grep %s' % guestname_backup)
        ret = process.run(check_status, shell=True, ignore_status=True)
        if not ret.exit_status:
            params['guestname'] = guestname_backup
            destroy.destroy(params)
            params['guestname'] = guestname
    check_status = ('virsh list --all|grep %s' % guestname)
    ret = process.run(check_status, shell=True, ignore_status=True)
    if not ret.exit_status:
        logger.info('destroy domain %s' % guestname)
        destroy.destroy(params)
        #check again ,in case the domain was not created by virt-clone
        check_status = ('virsh list --all|grep %s' % guestname)
        ret = process.run(check_status, shell=True, ignore_status=True)
        if not ret.exit_status:
            logger.info('undefine domain %s' % guestname)
            undefine.undefine(params)
    if os.path.exists(diskpath):
        logger.info('removing diskpath %s' % diskpath)
        os.remove(diskpath)
    logger.info('create domain %s' % guestname)
    clone_guest = ('virt-clone -o %s -n %s -f %s'
            % (guestname_backup, guestname, diskpath))
    ret = process.run(clone_guest, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error(str(ret.stderr))
        return 1
    logger.info('create domain %s' % guestname)
    chown_diskpath = ('chown qemu:qemu %s' % diskpath)
    ret = process.run(chown_diskpath, shell=True, ignore_status=True)
    if ret.exit_status:
        logger.error(str(ret.stderr))
        return 1
    start.start(params)
    return 0


def install_linux_clone_clean(params):
    """ clean testing environment """
    logger = params['logger']
    guestname = params.get('guestname')
    diskpath = params.get('diskpath', '/var/lib/libvirt/images/libvirt-test-api')

    install_common.clean_guest(guestname, logger)
    install_common.remove_all(diskpath, logger)

    cache_folder = utils.get_value_from_global("variables", "domain_cache_folder")
    install_common.remove_all(cache_folder + '/' + guestname + "_folder", logger)
