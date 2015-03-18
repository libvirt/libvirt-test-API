#!/usr/bin/env python
# To test "getSecurityModel"

import libvirt

from xml.dom import minidom
from libvirt import libvirtError
from src import sharedmod
from utils import utils

required_params = ('guestname',)
optional_params = {}

def get_security_driver(logger):
    """get security driver from /etc/libvirt/qemu.conf"""

    cmds = "grep \"^security_driver\" /etc/libvirt/qemu.conf"
    (ret, conf) = utils.exec_cmd(cmds, shell=True)
    if ret:
        cmds = "getenforce"
        (ret, policy) = utils.exec_cmd(cmds, shell=True)

        if policy[0] == "Disabled":
            return "none"
        else:
            return "selinux"

    tmp = conf[0].split(' = ')
    if len(tmp[1].split(', ')) > 1:
        driver = tmp[1].split(', ')
        return (filter(str.isalpha, driver[0]))
    else:
        cmds = "echo '%s' | awk -F '\"' '{print $2}'" % conf[0]
        (ret, driver) = utils.exec_cmd(cmds, shell=True)

        if driver[0] == "selinux":
            return "selinux"
        elif driver[0] == "none":
            return "none"
        elif driver[0] == "apparmor":
            return "apparmor"
        elif driver[0] == "stack":
            return "stack"
        else:
            return ""

def get_security_model(logger, domname):
    """get security model from process"""

    PID = "ps aux | grep -v grep | grep %s | awk '{print $2}'" % domname
    ret, pid = utils.exec_cmd(PID, shell=True)
    if ret:
        logger.error("get domain pid failed.")
        return ""

    LABEL = "ls -nZd /proc/%s" % pid[0]
    ret, label = utils.exec_cmd(LABEL, shell=True)
    if ret:
        logger.error("get domain process's label failed.")
        return ""

    if "system_u:system_r:svirt_t:s0" in label[0]:
        return "selinux"
    else:
        return "none"

def check_security_model(logger, domname, model):
    """ check security model"""

    dommodel = get_security_model(logger, domname)
    driver = get_security_driver(logger)

    logger.info("domain security model is %s." % dommodel)
    logger.info("get security driver is %s." % driver)
    logger.info("get security model is %s." % model)

    if driver == dommodel and dommodel == model:
        return True
    else:
        return False

def connection_security_model(params):
    """test API for getSecurityModel"""

    logger = params['logger']
    domname = params['guestname']
    conn = sharedmod.libvirtobj['conn']

    try:
        model = conn.getSecurityModel()

        if not check_security_model(logger, domname, model[0]):
            logger.error("Fail : get a error security model.")
            return 1
        else:
            logger.info("Pass : get security model successful.")
            return 0
    except libvirtError, e:
        logger.error("API error message: %s" % e.message)
        return 1
