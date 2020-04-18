# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
from libvirt import libvirtError

from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils, process

required_params = ('poolname',
                   'volname',
                   'cephserver',
                   'cephpool',
                   'flags',)
optional_params = {'snapshotname': ''}


def prepare_snapshot(cephserver, cephpool, volname, sn, logger):
    cmd = "rbd -m %s snap create %s/%s@%s" % (cephserver, cephpool, volname, sn)
    logger.debug("prepare_snapshot: cmd: %s" % cmd)
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status == 1:
        logger.error("prepare_snapshot: create snapshot failed")
        logger.error("out: %s" % ret.stdout)
        return 1

    return 0


def check_volume(cephserver, cephpool, volname, logger):
    cmd = "rbd -m %s -p %s ls | grep %s" % (cephserver, cephpool, volname)
    logger.debug("check_volume: cmd: %s" % cmd)
    ret = process.run(cmd, shell=True, ignore_status=True)
    if ret.exit_status == 0:
        logger.error("check_volume: delete failed, volume still exists.")
        logger.error("out: %s" % ret.stdout)
        return 1

    return 0


def delete_rbd_volume(params):
    """test volume delete with flags"""

    global logger
    logger = params['logger']
    poolname = params['poolname']
    volname = params['volname']
    sn = params.get('snapshotname', '')
    cephserver = params['cephserver']
    cephpool = params['cephpool']
    flags = params['flags']

    logger.info("the poolname is %s, volname is %s, snapshot name is %s" %
                (poolname, volname, sn))
    logger.info("ceph server is %s, ceph server pool is %s" %
                (cephserver, cephpool))
    logger.info("the flags given is %s" % flags)

    if sn:
        ret = prepare_snapshot(cephserver, cephpool, volname, sn, logger)
        if ret == 1:
            return 1

    try:
        conn = sharedmod.libvirtobj['conn']
        poolobj = conn.storagePoolLookupByName(poolname)
        vol = poolobj.storageVolLookupByName(volname)
        vol.delete(int(flags))

        if check_volume(cephserver, cephpool, volname, logger):
            return 1

    except libvirtError as e:
        logger.error("libvirt call failed: " + str(e))
        return 1

    return 0


def delete_rbd_volume_clean(params):
    global logger

    logger = params['logger']
    volname = params['volname']
    cephserver = params.get('cephserver', '')
    cephpool = params.get('cephpool', '')
    snapshotname = params.get('snapshotname', '')

    if snapshotname:
        cmd = ("rbd -m %s -p %s --image %s snap purge" %
               (cephserver, cephpool, volname))
        (ret, output) = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("Delete snapshot for %s failed." % volname)
            logger.error("Output: %s" % output)

    cmd = ("rbd -m %s -p %s ls | grep %s" %
           (cephserver, cephpool, volname))
    (ret, output) = utils.exec_cmd(cmd, shell=True)
    if not ret:
        cmd = "rbd -m %s -p %s remove %s" % (cephserver, cephpool, volname)
        (ret, output) = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("Remove %s failure." % volname)
