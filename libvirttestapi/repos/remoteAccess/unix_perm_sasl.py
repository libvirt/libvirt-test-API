#!/usr/bin/env python

import os
import time
import libvirt

from pwd import getpwnam
from libvirt import libvirtError
from libvirttestapi.utils import utils, process

required_params = ('auth_unix_ro', 'auth_unix_rw',)
optional_params = {'unix_sock_group': 'libvirt'}

TESTING_USER = 'testapi'
LIBVIRTD_CONF = "/etc/libvirt/libvirtd.conf"
SASLPASSWD2 = "/usr/sbin/saslpasswd2"
TICKET_CACHE = "/tmp/krb5cc_0"


def get_output(command, flag, logger):
    """execute shell command
    """
    ret = process.run(command, shell=True, ignore_status=True)
    if not flag and ret.exit_status:
        logger.error("executing " + "\"" + command + "\"" + " failed")
        logger.error(ret.stderr)
    return ret.exit_status, ret.stdout


def libvirt_configure(unix_sock_group, auth_unix_ro, auth_unix_rw, logger):
    """configure libvirt.conf """
    logger.info("configuring libvirt.conf")

    # uncomment unix_sock_group
    unix_group_add = "echo 'unix_sock_group = \"%s\"' >> %s" % \
        (unix_sock_group, LIBVIRTD_CONF)
    status, output = get_output(unix_group_add, 0, logger)
    if status:
        logger.error("setting unix_sock_group to %s failed" % unix_sock_group)
        return 1

    auth_unix_ro_add = "echo 'auth_unix_ro = \"%s\"' >> %s" % \
        (auth_unix_ro, LIBVIRTD_CONF)
    status, output = get_output(auth_unix_ro_add, 0, logger)
    if status:
        logger.error("setting auth_unix_ro to %s failed" % auth_unix_ro)
        return 1

    auth_unix_rw_add = "echo 'auth_unix_rw = \"%s\"' >> %s" % \
        (auth_unix_rw, LIBVIRTD_CONF)
    status, output = get_output(auth_unix_rw_add, 0, logger)
    if status:
        logger.error("setting auth_unix_rw to %s failed" % auth_unix_rw)
        return 1

    # restart remote libvirtd service
    libvirtd_restart_cmd = "service libvirtd restart"
    logger.info("libvirtd restart")
    status, output = get_output(libvirtd_restart_cmd, 0, logger)
    if status:
        logger.error("failed to restart libvirtd service")
        return 1

    logger.info("done to libvirtd configuration")
    return 0


def group_sasl_set(unix_sock_group, auth_unix_ro, auth_unix_rw, logger):
    """add libvirt group and set sasl authentication if needed"""
    logger.info("add unix socket group and sasl authentication if we need")

    # add unix socket group
    libvirt_group_add = "groupadd -f %s" % unix_sock_group
    if utils.Is_Fedora() or utils.isRelease("7", logger):
        libvirt_group_del = "groupdel %s" % unix_sock_group
    else:
        libvirt_group_del = "groupdel -f %s" % unix_sock_group

    group_check = "grep %s /etc/group" % unix_sock_group
    (status, output) = utils.exec_cmd(group_check, shell=True)
    # if the group already exists, remove it
    if not status:
        time.sleep(2)
        (status, output) = utils.exec_cmd(libvirt_group_del, shell=True)
        if status:
            logger.error("Fail to delete %s group: %s" % (unix_sock_group, output))
            return 1

    time.sleep(2)
    status, output = get_output(libvirt_group_add, 0, logger)
    if status:
        logger.error("failed to add %s group: %s" % (unix_sock_group, output))
        return 1

    time.sleep(2)
    # add "testapi" as the testing user
    libvirt_user_add = "useradd -g %s %s" % (unix_sock_group, TESTING_USER)
    status, output = get_output(libvirt_user_add, 0, logger)
    if status:
        logger.error("failed to add %s user into group %s" %
                     (TESTING_USER, unix_sock_group))
        return 1

    # add sasl user
    if auth_unix_ro == 'sasl' or auth_unix_rw == 'sasl':
        saslpasswd2_add = "echo %s | %s -a libvirt %s" % \
            (TESTING_USER, SASLPASSWD2, TESTING_USER)
        status, output = get_output(saslpasswd2_add, 0, logger)
        if status:
            logger.error("failed to set sasl user %s" % TESTING_USER)
            return 1

    return 0


def request_credentials(credentials, user_data):
    for credential in credentials:
        if credential[0] == libvirt.VIR_CRED_AUTHNAME:
            credential[4] = user_data[0]

            if len(credential[4]) == 0:
                credential[4] = credential[3]
        elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
            credential[4] = user_data[1]
        else:
            return -1

    return 0


def hypervisor_connecting_test(uri, unix_sock_group, auth_unix_ro, auth_unix_rw, logger):
    """connect to hypervisor"""
    logger.info("connect to hypervisor")
    orginal_user = os.geteuid()
    testing_user_id = getpwnam(TESTING_USER)[2]
    logger.info("the testing_user id is %d" % testing_user_id)

    logger.info("set euid to %d" % testing_user_id)
    os.seteuid(testing_user_id)

    if utils.version_compare("libvirt", 3, 2, 0, logger):
        cmd = "klist -A | grep 'Ticket cache: FILE:' | awk '{print $3}'"
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("get ticket cache file failed.")
            logger.error("cmd: %s" % cmd)
            logger.error("out: %s" % out)
            return 1

        TICKET_CACHE = out[0].split(':')[1]
        cmd = "chown %s:%s %s" % (TESTING_USER, unix_sock_group, TICKET_CACHE)
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("change %s owner failed." % TICKET_CACHE)
            return 1

    try:
        if auth_unix_ro == 'none':
            conn = libvirt.openReadOnly(uri)
        elif auth_unix_ro == 'sasl':
            user_data = [TESTING_USER, TESTING_USER]
            auth = [[libvirt.VIR_CRED_AUTHNAME,
                     libvirt.VIR_CRED_PASSPHRASE],
                    request_credentials, user_data]
            conn = libvirt.openAuth(uri, auth, 0)

        if auth_unix_rw == 'none':
            conn = libvirt.open(uri)
        elif auth_unix_rw == 'sasl':
            user_data = [TESTING_USER, TESTING_USER]
            auth = [[libvirt.VIR_CRED_AUTHNAME,
                     libvirt.VIR_CRED_PASSPHRASE],
                    request_credentials, user_data]
            conn = libvirt.openAuth(uri, auth, 0)
        conn.close()
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        logger.info("set euid back to %d" % orginal_user)
        os.seteuid(orginal_user)
        conn.close()
        return 1

    logger.info("set euid back to %d" % orginal_user)
    os.seteuid(orginal_user)
    return 0


def unix_perm_sasl(params):
    """ test unix socket group function and sasl authentication"""
    logger = params['logger']

    auth_unix_ro = params['auth_unix_ro']
    auth_unix_rw = params['auth_unix_rw']

    unix_sock_group = 'libvirt'
    if "unix_sock_group" in params:
        unix_sock_group = params['unix_sock_group']

    uri = "qemu:///system"

    if utils.version_compare("libvirt", 3, 2, 0, logger):
        cmd = ("sed -i 's/127.0.0.1   localhost/127.0.0.1   %s localhost/g'"
               " /etc/hosts" % utils.get_local_hostname())
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("set /etc/hosts failed: %s." % cmd)
            logger.error("out: %s" % out)
            return 1

        cmd = ("sed -i 's/::1         localhost/::1         %s localhost/g'"
               " /etc/hosts" % utils.get_local_hostname())
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("set /etc/hosts failed: %s." % cmd)
            logger.error("out: %s" % out)
            return 1

    if group_sasl_set(unix_sock_group, auth_unix_ro, auth_unix_rw, logger):
        return 1

    if libvirt_configure(unix_sock_group, auth_unix_ro, auth_unix_rw, logger):
        return 1

    if hypervisor_connecting_test(uri, unix_sock_group, auth_unix_ro, auth_unix_rw, logger):
        return 1

    return 0


def unix_perm_sasl_clean(params):
    """clean testing environment"""
    logger = params['logger']

    auth_unix_ro = params['auth_unix_ro']
    auth_unix_rw = params['auth_unix_rw']

    unix_sock_group = 'libvirt'
    if "unix_sock_group" in params:
        unix_sock_group = params['unix_sock_group']

    if utils.version_compare("libvirt", 3, 2, 0, logger):
        # change owner for ticker cache file
        cmd = "chown root:root %s" % TICKET_CACHE
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("change owner failed: %s" % out)

        hostname = utils.get_local_hostname()
        cmd = "sed -i 's/127.0.0.1   %s/127.0.0.1  /g' /etc/hosts" % hostname
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("set /etc/hosts failed: %s." % cmd)
            logger.error("out: %s" % out)

        cmd = "sed -i 's/::1         %s/::1        /g' /etc/hosts" % hostname
        ret, out = utils.exec_cmd(cmd, shell=True)
        if ret:
            logger.error("set /etc/hosts failed: %s." % cmd)
            logger.error("out: %s" % out)

    # delete "testapi" user
    libvirt_user_del = "userdel -f %s" % TESTING_USER
    status, output = get_output(libvirt_user_del, 0, logger)
    if status:
        logger.error("failed to del %s user: %s" % (TESTING_USER, output))

    # delete unix socket group
    libvirt_group_del = "groupdel -f %s" % unix_sock_group
    status, output = get_output(libvirt_group_del, 0, logger)
    if status:
        logger.error("failed to del %s group: %s" % (unix_sock_group, output))

    # delete sasl user
    if auth_unix_ro == 'sasl' or auth_unix_rw == 'sasl':
        saslpasswd2_delete = "%s -a libvirt -d %s" % (SASLPASSWD2, TESTING_USER)
        status, output = get_output(saslpasswd2_delete, 0, logger)
        if status:
            logger.error("failed to delete sasl user %s" % TESTING_USER)

    clean_libvirtd_conf = "sed -i -e :a -e '$d;N;2,3ba' -e 'P;D' %s" % \
                          LIBVIRTD_CONF
    utils.exec_cmd(clean_libvirtd_conf, shell=True)

    cmd = "service libvirtd restart"
    utils.exec_cmd(cmd, shell=True)

    return 0
