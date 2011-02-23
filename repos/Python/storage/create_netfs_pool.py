#!/usr/bin/env python
"""
    Testcase to create a netfs storage pool from an xml.
    Xml is built by this testcase by using the parameters.
"""

__author__   = 'Gurhan Ozen: gozen@redhat.com'
__date__     = 'Fri May 05, 2010'
__version__  = '0.1.0'
__credits__  = 'Copyright (C) 2010 Red Hat, Inc.'
__all__      = ['usage', 'check_pool', 'create_dir_pool']

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
from utils.Python import XMLParser
from exception import LibvirtAPI

def usage(params):
    """ 
       Verifies the params dictionary for the argument. Required arguments are
       poolname, pooltype, sourcename and sourcepath. 
  """

    logger = params['logger']

    # targetpath is optional, defaulted to /dev/disk/by-path
    keys = ['poolname', 'sourcename', 'sourcepath']
    for key in keys:
        if key not in params:
            logger.error("%s parameter is required. \
                          Please set it to a value" % key)
            return False
        elif len(params[key]) == 0:
            logger.error("%s key is empty, set it to a value" % key)
            return False
   
    #optional keys:
    if "pooltype" not in params:
        params['pooltype'] = 'netfs'

    # sanity check pooltype value:
    if params['pooltype'] == "netfs":
        return True
    else:
        logger.error("pooltype parameter must be either netfs")
        logger.error("it is: %s" % params['pooltype'])


def check_pool_create_libvirt(stgobj, poolname, logger):
    """Check the result of create storage pool inside libvirt """
    pool_names = stgobj.storage_pool_list()
    logger.info("poolnames is: %s " % pool_names)
    # check thru libvirt that it's really created..
    try:
        pool_names.index(poolname)
    except ValueError:
        logger.info("check_pool_create %s storage pool is \
                     UNSUCCESSFUL!!" % poolname)
        return False
    # check
    return True

def check_pool_create_OS(stgobj, poolname, logger):
    """This function will check if the poolname mount location is really mounted
       by the OS or not. """
    # we need to get where libvirt thinks the poolname is mounted to...
    poolxml = stgobj.dump_pool(poolname)
    # parse the xml to see where this is mounted...
    out = XMLParser.XMLParser().parse(poolxml)
    dest_path = out["target"]["path"]
    src_host = out["source"]["host"]["attr"]["name"]
    src_path = out["source"]["dir"]["attr"]["path"]
    logger.info("src host: %s src path: %s tgt path: %s" % \
                 (src_host, src_path, dest_path) )
    fd = open("/proc/mounts","r")
    mount = src_host + ":" + src_path
    pat = mount + "\s+" + dest_path
    found = 0
    for line in fd:
        if re.match(pat, line):
            found = 1
    fd.close()
    if found:
        return True
    else:
        return False
           
     

def display_pool_info(stg, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def create_netfs_pool(params):
    """ Create a network FS type storage pool from xml"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']
    
    util = utils.Utils()
    uri  = util.get_uri('127.0.0.1')
    
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    caps = conn.get_caps()
    logger.debug(caps)
    stgobj = storageAPI.StorageAPI(virconn)

    if check_pool_create_libvirt(stgobj, poolname, logger):
        logger.error("%s storage pool has already been created" % poolname)
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    poolxml = xmlobj.build_pool(params)
    logger.debug("storage pool xml:\n%s" % poolxml)

    try:
        logger.info("Creating %s storage pool" % poolname)
        stgobj.create_pool(poolxml)
        display_pool_info(stgobj, logger)
        if check_pool_create_libvirt(stgobj, poolname, logger):
            logger.info("creating %s storage pool is \
                         successful in libvirt" % poolname)
            if check_pool_create_OS(stgobj, poolname, logger):
                logger.info("creating %s storage pool is SUCCESSFUL!!!" % poolname)
                return 0
            else:
                logger.info("creating %s storage pool is \
                             UNSUCCESSFUL!!!" % poolname)
                return 1
        else:
            logger.info("creating %s storage pool is \
                         UNSUCCESSFUL in libvirt!!!" % poolname)
            return 1
    except LibvirtAPI, e:  
        logger.error("API error message: %s, error code is %s" % \
(e.response()['message'], e.response()['code']))
        return 1



      
