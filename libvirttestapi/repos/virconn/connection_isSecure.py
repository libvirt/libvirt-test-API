# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
from libvirt import libvirtError
from libvirttestapi.src import sharedmod


required_params = ()
optional_params = {}


def connection_isSecure(params):
    """Test if the connection to the hypervisor is secure

       Argument is a dictionary with one keys:
       {'logger': logger}

       Reture 0 on SUCCESS or 1 on FAILURE
    """

    logger = params['logger']

    conn = sharedmod.libvirtobj['conn']
    logger.info('Test if the connection to the hypervisor is secure')
    try:
        conn.isSecure()
    except libvirtError as e:
        logger.error("API error message: %s, error code is %s"
                     % (e.get_error_message(), e.get_error_code()))
        return 1
    logger.info('PASS')
    return 0
