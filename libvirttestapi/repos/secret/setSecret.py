# Test secret series command, check the set secret value, get secret value

import base64

from libvirttestapi.src import sharedmod
from xml.dom import minidom
from libvirt import libvirtError

required_params = ('secretUUID', 'value',)
optional_params = {}


def check_setSecret(value, secretobj, logger):
    """check whether the secret value is set correctly
    """
    secretvalue = secretobj.value(0)
    original_data = base64.decodestring(secretvalue).decode()
    if original_data == value:
        logger.info("Set secret value successfully")
        return 0
    else:
        logger.info("Set secret value failed")
        return 1


def setSecret(params):
    """set a secret value
    """
    logger = params['logger']
    secretUUID = params['secretUUID']
    value = params['value']

    data = base64.encodestring(value.encode()).decode('ascii')

    try:
        conn = sharedmod.libvirtobj['conn']
        secretobj = conn.secretLookupByUUIDString(secretUUID)
        private = minidom.parseString(secretobj.XMLDesc(0)).\
            getElementsByTagName('secret')[0].getAttribute('private')
        secretobj.setValue(data, 0)
        """if private is no, the value of secret can be get; if the private is
           yes, can't get the value of the secret.
        """
        if private == 'no':
            logger.info("the value of secret %s is %s" % (secretUUID,
                                                          secretobj.value(0).decode()))
            ret = check_setSecret(value, secretobj, logger)
            return ret
        else:
            logger.info("the value of secret %s is %s" % (secretUUID, data))
            logger.info("can not check the value via libvirt since secret %s "
                        "is private" % secretUUID)
            return 0

    except libvirtError as e:
        logger.error("libvirt call failed: " + e.get_error_message())
        return 1
