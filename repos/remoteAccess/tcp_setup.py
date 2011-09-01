#!/usr/bin/env python
""" Configure and test libvirt tcp connection
    remoteAccess:tcp_setup
        target_machine
            xx.xx.xx.xx
        username
            root
        password
            xxxxxx
        listen_tcp
            enable|disable
        auth_tcp
            none|sasl
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Sun Aug 7, 2011'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2011 Red Hat, Inc.'
__all__ = ['tcp_setup', 'tcp_libvirtd_set', 'hypervisor_connecting_test']

import os
import re
import sys

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib import connectAPI
from utils.Python import utils
from exception import LibvirtAPI

SASLPASSWD2 = "/usr/sbin/saslpasswd2"
LIBVIRTD_CONF = "/etc/libvirt/libvirtd.conf"
SYSCONFIG_LIBVIRTD = "/etc/sysconfig/libvirtd"

def check_params(params):
    """check out the arguments requried for this testcases"""
    logger = params['logger']
    keys = ['target_machine', 'username', 'password', 'listen_tcp', 'auth_tcp']
    for key in keys:
        if key not in params:
            logger.error("Argument %s is required" % key)
            return 1
    return 0

def sasl_user_add(target_machine, username, password, util, logger):
    """ execute saslpasswd2 to add sasl user """
    logger.info("add sasl user on server side")
    saslpasswd2_add = "echo %s | %s -a libvirt %s" % (password, SASLPASSWD2, username)
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                    password, saslpasswd2_add)
    if ret:
        logger.error("failed to add sasl user")
        return 1

    return 0

def tcp_libvirtd_set(target_machine, username, password,
                      listen_tcp, auth_tcp, util, logger):
    """ configure libvirtd.conf on libvirt server """
    logger.info("setting libvirtd.conf on libvirt server")
    # open libvirtd --listen option
    listen_open_cmd = "echo 'LIBVIRTD_ARGS=\"--listen\"' >> %s" % SYSCONFIG_LIBVIRTD
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                    password, listen_open_cmd)
    if ret:
        logger.error("failed to uncomment --listen in %s" % SYSCONFIG_LIBVIRTD)
        return 1

    # set listen_tls
    logger.info("set listen_tls to 0 in %s" % LIBVIRTD_CONF)
    listen_tls_disable = "echo \"listen_tls = 0\" >> %s" % LIBVIRTD_CONF
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                    password, listen_tls_disable)
    if ret:
        logger.error("failed to set listen_tls to 0 in %s" % LIBVIRTD_CONF)
        return 1

    # set listen_tcp
    if listen_tcp == 'enable':
        logger.info("enable listen_tcp = 1 in %s" % LIBVIRTD_CONF)
        listen_tcp_set = "echo 'listen_tcp = 1' >> %s" % LIBVIRTD_CONF
        ret, output = util.remote_exec_pexpect(target_machine, username,
                                        password, listen_tcp_set)
        if ret:
            logger.error("failed to set listen_tcp in %s" % LIBVIRTD_CONF)
            return 1

    # set auth_tcp
    logger.info("set auth_tcp to \"%s\" in %s" % (auth_tcp, LIBVIRTD_CONF))
    auth_tcp_set = "echo 'auth_tcp = \"%s\"' >> %s" % (auth_tcp, LIBVIRTD_CONF)
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                       password, auth_tcp_set)
    if ret:
        logger.error("failed to set auth_tcp in %s" % LIBVIRTD_CONF)
        return 1

    # restart remote libvirtd service
    libvirtd_restart_cmd = "service libvirtd restart"
    logger.info("libvirtd restart")
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                    password, libvirtd_restart_cmd)
    if ret:
        logger.error("failed to restart libvirtd service")
        return 1

    logger.info("done to libvirtd configuration")
    return 0

def request_credentials(credentials, user_data):
    for credential in credentials:
        if credential[0] == connectAPI.VIR_CRED_AUTHNAME:
            credential[4] = user_data[0]

            if len(credential[4]) == 0:
                credential[4] = credential[3]
        elif credential[0] == connectAPI.VIR_CRED_PASSPHRASE:
            credential[4] = user_data[1]
        else:
            return -1

    return 0

def hypervisor_connecting_test(uri, auth_tcp, username,
                                password, logger, expected_result):
    """ connect remote server """
    ret = 1
    try:
        conn = connectAPI.ConnectAPI()
        if auth_tcp == 'none':
            virconn = conn.open(uri)
        elif auth_tcp == 'sasl':
            user_data = [username, password]
            auth = [[connectAPI.VIR_CRED_AUTHNAME, connectAPI.VIR_CRED_PASSPHRASE], request_credentials, user_data]
            virconn = conn.openAuth(uri, auth, 0)

        ret = 0
        conn.close()
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))

        ret = 1
        conn.close()

    if ret == 0 and expected_result == 'success':
        logger.info("tcp connnection success")
        return 0
    elif ret == 1 and expected_result == 'fail':
        logger.info("tcp connection failed, but that is expected")
        return 0
    elif ret == 0 and expected_result == 'fail':
        logger.error("tcp connection success, but we hope the reverse")
        return 1
    elif ret == 1 and expected_result == 'success':
        logger.error("tcp connection failed")
        return 1

    return 0

def tcp_setup(params):
    """ configure libvirt and connect to it through TCP socket"""
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    target_machine = params['target_machine']
    username = params['username']
    password = params['password']
    listen_tcp = params['listen_tcp']
    auth_tcp = params['auth_tcp']

    uri = "qemu+tcp://%s/system" % target_machine

    util = utils.Utils()

    logger.info("the hostname of server is %s" % target_machine)
    logger.info("the value of listen_tcp is %s" % listen_tcp)
    logger.info("the value of auth_tcp is %s" % auth_tcp)

    if not util.do_ping(target_machine, 0):
        logger.error("failed to ping host %s" % target_machine)
        return 1

    if auth_tcp == 'sasl':
        if sasl_user_add(target_machine, username, password, util, logger):
            return 1

    if tcp_libvirtd_set(target_machine, username, password,
                         listen_tcp, auth_tcp, util, logger):
        return 1

    if listen_tcp == 'disable':
        if hypervisor_connecting_test(uri, auth_tcp, username,
                                       password, logger, 'fail'):
            return 1
    elif listen_tcp == 'enable':
        if hypervisor_connecting_test(uri, auth_tcp, username,
                                       password, logger, 'success'):
            return 1

    return 0

def tcp_setup_clean(params):
    """cleanup testing environment"""

    logger = params['logger']
    target_machine = params['target_machine']
    username = params['username']
    password = params['password']
    listen_tcp = params['listen_tcp']
    auth_tcp = params['auth_tcp']

    util = utils.Utils()

    if auth_tcp == 'sasl':
        saslpasswd2_delete = "%s -a libvirt -d %s" % (SASLPASSWD2, username)
        ret, output = util.remote_exec_pexpect(target_machine, username,
                                        password, saslpasswd2_delete)
        if ret:
            logger.error("failed to delete sasl user")
    libvirtd_conf_retore = "sed -i -n '/^[ #]/p' %s" % LIBVIRTD_CONF
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                    password, libvirtd_conf_retore)
    if ret:
        logger.error("failed to restore %s" % LIBVIRTD_CONF)

    sysconfig_libvirtd_restore = "sed -i -n '/^[ #]/p' %s" % SYSCONFIG_LIBVIRTD
    ret, output = util.remote_exec_pexpect(target_machine, username,
                                    password, sysconfig_libvirtd_restore)
    if ret:
        logger.error("failed to restore %s" % SYSCONFIG_LIBVIRTD)
