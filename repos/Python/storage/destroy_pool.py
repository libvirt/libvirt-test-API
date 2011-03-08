#!/usr/bin/env python
"""
    Testcase to destroy a storage pool. It'll take a poolname and try to destroy
    it. The sanity checking will only be done to see if the a pool with the
    given poolname exists or not. It won't check if the pool is active or not.
"""

__author__   = 'Gurhan Ozen: gozen@redhat.com'
__date__     = 'Fri May 07, 2010'
__version__  = '0.1.0'
__credits__  = 'Copyright (C) 2010 Red Hat, Inc.'
__all__      = ['usage', 'check_pool_destroy', 'destroy_pool']

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

from lib.Python import connectAPI
from lib.Python import storageAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage(params):
    """Does a sanity check on the parameters given"""
    logger = params['logger']
    # poolname is the only required parameter
    if 'poolname' not in params:
        logger.error("poolname argument is needed. Please provide one")
        return False
    elif len(params['poolname']) == 0:
        logger.error("poolname parameter is empty. Please set it")
        return False

    return True

def check_pool_existence(stgobj, poolname, logger):
    """
     Check to verify that there indeed is a pool named with the given poolname
    """
    pool_names =  stgobj.storage_pool_list()
    pool_names += stgobj.defstorage_pool_list()

    if poolname not in pool_names:
        logger.error("%s doesn't seem to be a right poolname" % poolname)
        return False

    return True

def check_pool_destroy(stgobj, poolname, logger):
    """
     Check to verify that the pool is actually gone
    """
    pool_names = stgobj.storage_pool_list()

    if poolname not in pool_names:
        logger.info("destroy pool %s SUCCESS , " % poolname)
        logger.info("%s doesn't seem to be an active poolname anymore, " % \
                     poolname)
        return True
    else:
        logger.error("destroy pool %s UNSUCCESSFUL" % poolname)
        logger.error("%s is still in the list after destroy" % poolname)
        return True

def destroy_pool(params):
    """Function to actually destroy the pool"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    stgobj = storageAPI.StorageAPI(virconn)

    if check_pool_existence(stgobj, poolname, logger):
        # Make sure that the pool is active.
        if stgobj.isActive_pool(poolname):
            try:
                # Go ahead and try to destroy the pool..
                stgobj.destroy_pool(poolname)
                # Check in libvirt to make sure that it's really destroyed..
                if not check_pool_destroy(stgobj, poolname, logger):
                    print("%s doesn't seem to be destroyed properly" % poolname)
                    return 1
                else:
                    print("%s is destroyed!!!" % poolname)
                    return 0
            except LibvirtAPI, e:
                logger.error("API error message: %s, error code is %s" % \
                             (e.response()['message'], e.response()['code']))
                return 1
        else:
            logger.error("%s is not active. \
                          It must be active to be destroyed." % poolname)
            return 1
