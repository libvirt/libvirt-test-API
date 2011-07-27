#!/usr/bin/env python
""" Setup tls authentication between two hosts and configure libvirt
    to use it for connection.
    remoteAccess:tls_setup
        target_machine
            xx.xx.xx.xx
        username
            root
        password
            xxxxxx
        pkipath(optional)
            /tmp/pkipath
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Mon July 25, 2011'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2011 Red Hat, Inc.'
__all__ = ['usage']

import os
import re
import sys
import pexpect
import string
import commands
import shutil

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

CERTTOOL = "/usr/bin/certtool"
CP = "/bin/cp"
MKDIR = "/bin/mkdir"
CA_FOLDER = "/etc/pki/CA"
PRIVATE_KEY_FOLDER = "/etc/pki/libvirt/private"
CERTIFICATE_FOLDER = "/etc/pki/libvirt"

TEMP_TLS_FOLDER = "/tmp/libvirt_test_API_tls"
CAKEY = os.path.join(TEMP_TLS_FOLDER, 'cakey.pem')
CACERT = os.path.join(TEMP_TLS_FOLDER, 'cacert.pem')
SERVERKEY = os.path.join(TEMP_TLS_FOLDER, 'serverkey.pem')
SERVERCERT = os.path.join(TEMP_TLS_FOLDER, 'servercert.pem')
CLIENTKEY = os.path.join(TEMP_TLS_FOLDER, 'clientkey.pem')
CLIENTCERT = os.path.join(TEMP_TLS_FOLDER, 'clientcert.pem')

def check_params(params):
    """check out the arguments requried for migration"""
    logger = params['logger']
    keys = ['target_machine', 'username', 'password']
    for key in keys:
        if key not in params:
            logger.error("Argument %s is required" % key)
            return 1
    return 0

def CA_setting_up(util, logger):
    """ setting up a Certificate Authority """
    # Create a private key for CA
    logger.info("generate CA certificates")

    cakey_fd = open(CAKEY, 'w')
    ret, out = util.exec_cmd([CERTTOOL, '--generate-privkey'], outfile=cakey_fd)
    cakey_fd.close()
    if ret != 0:
        logger.error("failed to create CA private key")
        return 1


    # ca.info file
    cainfo = os.path.join(TEMP_TLS_FOLDER, 'ca.info')
    cainfo_fd = open(cainfo, 'w')
    cainfo_str = "cn = Libvirt_test_API\n"  + \
                 "ca\n"                     + \
                 "cert_signing_key\n"

    cainfo_fd.write(cainfo_str)
    cainfo_fd.close()

    # Generate cacert.pem
    cacert_args = [CERTTOOL, '--generate-self-signed', '--load-privkey', CAKEY, '--template', cainfo]
    cacert_fd = open(CACERT, 'w')
    ret, out = util.exec_cmd(cacert_args, outfile=cacert_fd)
    cacert_fd.close()
    if ret != 0:
        logger.error("failed to create cacert.pem")
        return 1

    logger.info("done the CA certificates job")
    return 0

def tls_server_cert(target_machine, util, logger):
    """ generating server certificates """
    # Create tls server key
    logger.info("generate server certificates")

    serverkey_fd = open(SERVERKEY, 'w')
    ret, out = util.exec_cmd([CERTTOOL, '--generate-privkey'], outfile=serverkey_fd)
    serverkey_fd.close()
    if ret != 0:
        logger.error("failed to create server key")
        return 1

    # server.info
    serverinfo = os.path.join(TEMP_TLS_FOLDER, 'server.info')
    serverinfo_fd = open(serverinfo, 'w')
    serverinfo_str = "organization = Libvirt_test_API\n" + \
                     "cn = %s\n" % target_machine        + \
                     "tls_www_server\n"                  + \
                     "encryption_key\n"                  + \
                     "signing_key\n"

    serverinfo_fd.write(serverinfo_str)
    serverinfo_fd.close()

    # Generate servercert.pem
    servercert_args = [CERTTOOL,
                       '--generate-certificate',
                       '--load-privkey', SERVERKEY,
                       '--load-ca-certificate', CACERT,
                       '--load-ca-privkey', CAKEY,
                       '--template', serverinfo
                      ]
    servercert_fd = open(SERVERCERT, 'w')
    ret, out = util.exec_cmd(servercert_args, outfile=servercert_fd)
    servercert_fd.close()
    if ret != 0:
        logger.error("failed to create servercert.pem")
        return 1

    logger.info("done the server certificates job")
    return 0

def tls_client_cert(local_machine, util, logger):
    """ generating client certificates """
    # Create tls client key
    logger.info("generate client certificates")

    clientkey_fd = open(CLIENTKEY, 'w')
    ret, out = util.exec_cmd([CERTTOOL, '--generate-privkey'], outfile=clientkey_fd)
    clientkey_fd.close()
    if ret != 0:
        logger.error("failed to create client key")
        return 1

    # client.info
    clientinfo = os.path.join(TEMP_TLS_FOLDER, 'client.info')
    clientinfo_fd = open(clientinfo, 'w')
    clientinfo_str = "country = xxx\n"                   + \
                     "state = xxx\n"                     + \
                     "locality = xxx\n"                  + \
                     "organization = Libvirt_test_API\n" + \
                     "cn = %s\n" % local_machine         + \
                     "tls_www_client\n"                  + \
                     "encryption_key\n"                  + \
                     "signing_key\n"

    clientinfo_fd.write(clientinfo_str)
    clientinfo_fd.close()

    # Generate clientcert.pem
    clientcert_args = [CERTTOOL,
                       '--generate-certificate',
                       '--load-privkey', CLIENTKEY,
                       '--load-ca-certificate', CACERT,
                       '--load-ca-privkey', CAKEY,
                       '--template', clientinfo,
                      ]

    clientcert_fd = open(CLIENTCERT, 'w')
    ret, out = util.exec_cmd(clientcert_args, outfile=clientcert_fd)
    clientcert_fd.close()
    if ret != 0:
        logger.error("failed to create client certificates")
        return 1

    logger.info("done the client certificates job")
    return 0

def deliver_cert(target_machine, username, password, pkipath, util, logger):
    """ deliver CA, server and client certificates """
    # transmit cacert.pem to remote host
    logger.info("deliver CA, server and client certificates to both local and remote server")
    ret = util.scp_file(target_machine, username, password, CA_FOLDER, CACERT)
    if ret:
        logger.error("scp cacert.pem to %s error" % target_machine)
        return 1

    # copy cacert.pem to local CA folder
    cacert_cp = [CP, '-f', CACERT, (pkipath and pkipath) or CA_FOLDER]
    ret, out = util.exec_cmd(cacert_cp)
    if ret:
        logger.error("copying cacert.pem to %s error" % CA_FOLDER)
        return 1

    # mkdir /etc/pki/libvirt/private on remote host
    libvirt_priv_cmd = "mkdir -p %s" % PRIVATE_KEY_FOLDER
    ret = util.remote_exec_pexpect(target_machine, username, password, libvirt_priv_cmd)
    if ret:
        logger.error("failed to make /etc/pki/libvirt/private on %s" % target_machine)
        return 1

    # transmit serverkey.pem to remote host
    ret = util.scp_file(target_machine, username, password, PRIVATE_KEY_FOLDER, SERVERKEY)
    if ret:
        logger.error("failed to scp serverkey.pem to %s" % target_machine)
        return 1

    # transmit servercert.pem to remote host
    ret = util.scp_file(target_machine, username, password, CERTIFICATE_FOLDER, SERVERCERT)
    if ret:
        logger.error("failed to scp servercert.pem to %s" % target_machine)
        return 1

    libvirt_priv_cmd_local = [MKDIR, '-p', PRIVATE_KEY_FOLDER]
    ret, out = util.exec_cmd(libvirt_priv_cmd_local)
    if ret:
        logger.error("failed to make %s on local" % PRIVATE_KEY_FOLDER)
        return 1

    # copy clientkey.pem to local folder
    clientkey_cp = [CP, '-f', CLIENTKEY, (pkipath and pkipath) or PRIVATE_KEY_FOLDER]
    ret, out = util.exec_cmd(clientkey_cp)
    if ret:
        logger.error("failed to copy clientkey.pem to %s" % PRIVATE_KEY_FOLDER)
        return 1

    # copy clientcert.pem to local folder
    clientcert_cp = [CP, '-f', CLIENTCERT, (pkipath and pkipath) or CERTIFICATE_FOLDER]
    ret, out = util.exec_cmd(clientcert_cp)
    if ret:
        logger.error("failed to copy clientcert.pem to %s" % CERTIFICATE_FOLDER)
        return 1

    logger.info("done to delivery")
    return 0

def tls_libvirtd_set(target_machine, username, password, util, logger):
    """ configure libvirtd.conf on tls server """
    logger.info("setting libvirtd.conf on tls server")
    # open libvirtd --listen option
    listen_open_cmd = "echo 'LIBVIRTD_ARGS=\"--listen\"' >> /etc/sysconfig/libvirtd"
    ret = util.remote_exec_pexpect(target_machine, username, password, listen_open_cmd)
    if ret:
        logger.error("failed to uncomment --listen in /etc/sysconfig/libvirtd")
        return 1

    listen_tcp_cmd = "echo \"listen_tcp = 1\" >> /etc/libvirt/libvirtd.conf"
    ret = util.remote_exec_pexpect(target_machine, username, password, listen_tcp_cmd)
    if ret:
        logger.error("failed to uncomment listen_tcp in /etc/libvirt/libvirtd.conf")
        return 1

    # restart remote libvirtd service
    libvirtd_restart_cmd = "service libvirtd restart"
    ret = util.remote_exec_pexpect(target_machine, username, password, libvirtd_restart_cmd)
    if ret:
        logger.error("failed to restart libvirtd service")
        return 1

    logger.info("done to libvirtd configuration")
    return 0

def iptables_stop(target_machine, username, password, util, logger):
    """ This is a temprory method in favor of migration """
    logger.info("stop local and remote iptables temprorily")
    iptables_stop_cmd = "service iptables stop"
    ret = util.remote_exec_pexpect(target_machine, username, password, iptables_stop_cmd)
    if ret:
        logger.error("failed to stop remote iptables service")
        return 1

    iptables_stop = ["service", "iptables", "stop"]
    ret, out = util.exec_cmd(iptables_stop)
    if ret:
        logger.error("failed to stop local iptables service")
        return 1

    logger.info("done the iptables stop job")
    return 0

def tls_setup(params):
    """ generate tls certificates and configure libvirt """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    target_machine = params['target_machine']
    username = params['username']
    password = params['password']

    pkipath = ""
    if params.has_key('pkipath'):
        pkipath = params['pkipath']
        if os.path.exists(pkipath):
            shutil.rmtree(pkipath)

        os.mkdir(pkipath)

    util = utils.Utils()
    local_machine = util.get_local_hostname()

    logger.info("the hostname of server is %s" % target_machine)
    logger.info("the hostname of local machine is %s" % local_machine)

    if not util.do_ping(target_machine, 0):
        logger.error("failed to ping host %s" % target_machine)
        return 1

    if os.path.exists(TEMP_TLS_FOLDER):
        shutil.rmtree(TEMP_TLS_FOLDER)

    os.mkdir(TEMP_TLS_FOLDER)

    if iptables_stop(target_machine, username, password, util, logger):
        return 1

    if CA_setting_up(util, logger):
        return 1

    if tls_server_cert(target_machine, util, logger):
        return 1

    if tls_client_cert(local_machine, util, logger):
        return 1

    if deliver_cert(target_machine, username, password, pkipath, util, logger):
        return 1

    if tls_libvirtd_set(target_machine, username, password, util, logger):
        return 1

    uri = "qemu://%s/system" % target_machine
    if pkipath:
        uri += "?pkipath=%s" % pkipath

    try:
        conn = connectAPI.ConnectAPI()
        virconn = conn.open(uri)
        virconn.close()
        logger.info("tls authentication success")
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("tls authentication failed")
        return 1

    return 0

def tls_setup_clean(params):
    """ cleanup testing enviroment """
    if os.path.exists(TEMP_TLS_FOLDER):
        shutil.rmtree(TEMP_TLS_FOLDER)

    logger = params['logger']
    target_machine = params['target_machine']
    username = params['username']
    password = params['password']

    util = utils.Utils()
    cacert_rm = "rm -f %s/cacert.pem" % CA_FOLDER
    ret = util.remote_exec_pexpect(target_machine, username, password, cacert_rm)
    if ret:
        logger.error("failed to remove cacert.pem on remote machine")

    ca_libvirt_rm = "rm -rf %s" % CERTIFICATE_FOLDER
    ret = util.remote_exec_pexpect(target_machine, username, password, ca_libvirt_rm)
    if ret:
        logger.error("failed to remove libvirt folder")

    os.remove("%s/cacert.pem" % CA_FOLDER)
    shutil.rmtree(CERTIFICATE_FOLDER)

