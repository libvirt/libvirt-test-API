# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# To test "getSecurityModel"

import libvirt

from libvirt import libvirtError
from libvirttestapi.src import sharedmod
from libvirttestapi.utils import utils

required_params = ()
optional_params = {'uri': ''}


def get_security_driver(logger):
    """get security driver from /etc/libvirt/qemu.conf"""

    cmds = "getenforce"
    (ret, policy) = utils.exec_cmd(cmds, shell=True)

    if policy[0] == "Disabled":
        logger.info("For selinux disbled status, security driver is 'none'.")
        return "none"

    cmds = "grep \"^security_driver\" /etc/libvirt/qemu.conf"
    (ret, conf) = utils.exec_cmd(cmds, shell=True)
    if ret:
        logger.info("Get default secutiry driver is 'selinux'.")
        return "selinux"

    tmp = conf[0].split(' = ')
    if len(tmp[1].split(', ')) > 1:
        driver = tmp[1].split(', ')
        logger.info("Get secutiry driver is %s." % filter(str.isalpha, driver[0]))
        return (filter(str.isalpha, driver[0]))
    else:
        cmds = "echo '%s' | awk -F '\"' '{print $2}'" % conf[0]
        (ret, driver) = utils.exec_cmd(cmds, shell=True)
        logger.info("Get secutiry driver is %s." % driver[0])

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


def connection_security_model(params):
    """test API for getSecurityModel"""

    logger = params['logger']
    uri = params.get("uri", None)

    if 'uri' in params:
        conn = libvirt.open(uri)
    else:
        conn = sharedmod.libvirtobj['conn']

    try:
        model = conn.getSecurityModel()
        logger.info("model : %s" % model)
        driver = get_security_driver(logger)
        if driver == model[0]:
            logger.info("Pass : get security model successful.")
            return 0
        else:
            logger.error("Fail : get security model failed.")
            return 1

    except libvirtError as e:
        logger.error("API error message: %s" % e.get_error_message())
        return 1
