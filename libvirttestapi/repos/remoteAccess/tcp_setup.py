# To test connection via tcp protocol

import libvirt
import time

from libvirt import libvirtError
from libvirttestapi.utils import utils
from libvirttestapi.repos.remoteAccess import remote_common

required_params = ('target_machine',
                   'username',
                   'password',
                   'listen_tcp',
                   'auth_tcp',)
optional_params = {}

SASLPASSWD2 = "/usr/sbin/saslpasswd2"
LIBVIRTD_CONF = "/etc/libvirt/libvirtd.conf"
SYSCONFIG_LIBVIRTD = "/etc/sysconfig/libvirtd"


def sasl_user_add(target_machine, username, password, logger):
    """ execute saslpasswd2 to add sasl user """
    logger.info("add sasl user on server side")
    saslpasswd2_add = "echo %s | %s -a libvirt %s" % (password, SASLPASSWD2, username)
    ret, output = utils.remote_exec_pexpect(target_machine, username,
                                            password, saslpasswd2_add)
    if ret:
        logger.error("failed to add sasl user")
        return 1

    return 0


def tcp_libvirtd_set(target_machine, username, password,
                     listen_tcp, auth_tcp, logger):
    """ configure libvirtd.conf on libvirt server """
    logger.info("setting libvirtd.conf on libvirt server")
    if listen_tcp == "enable":
        # open libvirtd --listen option
        listen_open_cmd = 'echo "LIBVIRTD_ARGS=\\\"--listen\\\"" >> %s' % SYSCONFIG_LIBVIRTD
        ret, output = utils.remote_exec_pexpect(target_machine, username,
                                                password, listen_open_cmd)
        if ret:
            logger.error("failed to add '--listen' in %s" % SYSCONFIG_LIBVIRTD)
            return 1

    # set listen_tls
    logger.info("set listen_tls to 0 in %s" % LIBVIRTD_CONF)
    listen_tls_disable = "echo \"listen_tls = 0\" >> %s" % LIBVIRTD_CONF
    ret, output = utils.remote_exec_pexpect(target_machine, username,
                                            password, listen_tls_disable)
    if ret:
        logger.error("failed to set listen_tls to 0 in %s" % LIBVIRTD_CONF)
        return 1

    # set listen_tcp
    if listen_tcp == 'enable':
        logger.info("set listen_tcp = 1 in %s" % LIBVIRTD_CONF)
        listen_tcp_set = "echo 'listen_tcp = 1' >> %s" % LIBVIRTD_CONF
        ret, output = utils.remote_exec_pexpect(target_machine, username,
                                                password, listen_tcp_set)
        if ret:
            logger.error("failed to set listen_tcp in %s" % LIBVIRTD_CONF)
            return 1
    elif listen_tcp == 'disable':
        logger.info("set listen_tcp = 0 in %s" % LIBVIRTD_CONF)
        listen_tcp_set = "echo 'listen_tcp = 0' >> %s" % LIBVIRTD_CONF
        ret, output = utils.remote_exec_pexpect(target_machine, username,
                                                password, listen_tcp_set)
        if ret:
            logger.error("failed to set listen_tcp in %s" % LIBVIRTD_CONF)
            return 1

    # set auth_tcp
    logger.info("set auth_tcp to \"%s\" in %s" % (auth_tcp, LIBVIRTD_CONF))
    auth_tcp_set = 'echo "auth_tcp = \\\"%s\\\"" >> %s' % (auth_tcp, LIBVIRTD_CONF)
    ret, output = utils.remote_exec_pexpect(target_machine, username,
                                            password, auth_tcp_set)
    if ret:
        logger.error("failed to set auth_tcp in %s" % LIBVIRTD_CONF)
        return 1

    # Restart remote libvirtd
    if remote_common.restart_remote_libvirtd(target_machine, username,
                                             password, logger, 'tcp'):
        return 1

    time.sleep(3)
    logger.info("Done to libvirtd configuration")
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


def hypervisor_connecting_test(uri, auth_tcp, username,
                               password, logger, expected_result):
    """ connect remote server """
    ret = 1
    try:
        if auth_tcp == 'none':
            logger.debug("call libvirt.open()")
            conn = libvirt.open(uri)
        elif auth_tcp == 'sasl':
            user_data = [username, password]
            auth = [[libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE], request_credentials, user_data]
            logger.debug("call libvirt.openAuth()")
            conn = libvirt.openAuth(uri, auth, 0)

        ret = 0
        conn.close()
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        ret = 1

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
    """
    Prepare and test tcp env
    """
    logger = params['logger']
    target_machine = params['target_machine']
    username = params['username']
    password = params['password']
    listen_tcp = params['listen_tcp']
    auth_tcp = params['auth_tcp']

    target_hostname = utils.get_target_hostname(target_machine, username, password, logger)
    uri = "qemu+tcp://%s/system" % target_hostname

    logger.info("Target hostname: %s" % target_machine)
    logger.info("listen_tcp: %s" % listen_tcp)
    logger.info("auth_tcp: %s" % auth_tcp)

    if utils.version_compare('libvirt-python', 5, 6, 0, logger):
        logger.info("Because of bug 1741403, change listen_tcp to disable.")
        listen_tcp = "disable"

    if not utils.do_ping(target_machine, 0):
        logger.error("Failed to ping host %s" % target_machine)
        return 1

    if auth_tcp == 'sasl':
        if sasl_user_add(target_machine, username, password, logger):
            return 1

    if remote_common.set_firewall('16509/tcp', target_machine, username, password, logger):
        return 1

    if tcp_libvirtd_set(target_machine, username, password,
                        listen_tcp, auth_tcp, logger):
        return 1

    if listen_tcp == 'disable':
        if utils.version_compare('libvirt-python', 5, 6, 0, logger):
            if hypervisor_connecting_test(uri, auth_tcp, username,
                                          password, logger, 'success'):
                return 1
        else:
            if hypervisor_connecting_test(uri, auth_tcp, username,
                                          password, logger, 'fail'):
                return 1
    elif listen_tcp == 'enable':
        if hypervisor_connecting_test(uri, auth_tcp, username,
                                      password, logger, 'success'):
            return 1

    return 0


def tcp_setup_clean(params):
    """
    Cleanup testing environment.
    """
    logger = params['logger']
    target_machine = params['target_machine']
    username = params['username']
    password = params['password']
    listen_tcp = params['listen_tcp']
    auth_tcp = params['auth_tcp']

    if auth_tcp == 'sasl':
        cmd = "%s -a libvirt -d %s" % (SASLPASSWD2, username)
        ret, output = utils.remote_exec_pexpect(target_machine, username,
                                                password, cmd)
        if ret:
            logger.error("Failed to delete sasl user.")
    cmd = "sed -i -n \"/^[ #]/p\" %s" % LIBVIRTD_CONF
    ret, output = utils.remote_exec_pexpect(target_machine, username,
                                            password, cmd)
    if ret:
        logger.error("Failed to restore %s." % LIBVIRTD_CONF)

    cmd = "sed -i -n \"/^[ #]/p\" %s" % SYSCONFIG_LIBVIRTD
    ret, output = utils.remote_exec_pexpect(target_machine, username,
                                            password, cmd)
    if ret:
        logger.error("Failed to restore %s." % SYSCONFIG_LIBVIRTD)

    # Restart remote libvirtd
    remote_common.restart_remote_libvirtd(target_machine, username,
                                          password, logger, 'tcp')
