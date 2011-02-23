#!/usr/bin/env python
"""testing "virsh domblkinfo" function
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Tue Jan 18, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['domname']


import os
import sys
import re
import commands

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
from lib.Python import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

GET_DOMBLKINFO_MAC = "virsh domblkinfo %s %s | awk '{print $2}'" 
GET_CAPACITY = "du -b %s | awk '{print $1}'" 
GET_PHYSICAL_K = " du -B K %s | awk '{print $1}'"
VIRSH_DOMBLKINFO = "virsh domblkinfo %s %s"


def check_params(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    options = ['guestname', 'blockdev']
    for option in options:
        if option not in params:
            logger.error("option %s is required" % option)
            return 1

def get_output(command, logger):
    """execute shell command
    """
    status, ret = commands.getstatusoutput(command)
    if status:
        logger.error("executing "+ "\"" +  command  + "\"" + " failed")
        logger.error(ret)
    return status, ret

def check_domain_exists(domobj, guestname, logger):
    """ check if the domain exists, may or may not be active """
    guest_names = domobj.get_list()
    guest_names += domobj.get_defined_list()

    if guestname not in guest_names:
        logger.error("%s doesn't exist" % guestname)
        return False
    else:
        return True

def check_block_data(blockdev, blkdata, logger):
    """ check data about capacity,allocation,physical """
    status, apparent_size = get_output(GET_CAPACITY % blockdev, logger)
    if not status:
        if apparent_size == blkdata[0]:
            logger.info("the capacity of '%s' is %s, checking succeeded" % \
                        (blockdev, apparent_size))
        else:
            logger.error("apparent-size from 'du' is %s, \n\
                         but from 'domblkinfo' is %s, checking failed" % \
                        (apparent_size, blkdata[0])) 
            return 1
    else:
        return 1

    status, block_size_k = get_output(GET_PHYSICAL_K % blockdev, logger)
    if not status:
        block_size_b = int(block_size_k[:-1]) * 1024     
        # temporarily, we only test the default case, assuming
        # Allocation value is equal to Physical value
        if str(block_size_b) == blkdata[1] and str(block_size_b) == blkdata[2]:
            logger.info("the block size of '%s' is %s, same with \n\
                        Allocation and Physical value, checking succeeded" % \
                         (blockdev, block_size_b))
        else:
            logger.error("the block size from 'du' is %s, \n\
                          the Allocation value is %s, Physical value is %s, \n\
                          checking failed" % (block_size_b, blkdata[1], blkdata[2]))
            return 1

    return 0
 

def domblkinfo(params):
    """ using du command to check the data
        in the output of virsh domblkinfo
    """
    logger = params['logger']

    logger.info("Checking the validation of arguments provided.")
    params_check_result = check_params(params)

    if params_check_result:
        return 1
        
    logger.info("Arguments checkup completed.")

    guestname = params.get('guestname')
    blockdev = params.get('blockdev')

    logger.info("the name of guest is %s" % guestname)
    logger.info("the block device is %s" % blockdev)

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)

    if not check_domain_exists(domobj, guestname, logger):
        logger.error("need a defined guest, may or may not be active")
        return 1

    logger.info("the output of virsh domblkinfo is:")
    status, output = get_output(VIRSH_DOMBLKINFO % (guestname, blockdev), logger)
    if not status:
        logger.info("\n" + output)
    else:
        return 1

    status, data_str = get_output(GET_DOMBLKINFO_MAC % (guestname, blockdev), logger)    
    if not status:
        blkdata = data_str.rstrip().split('\n')
        logger.info("capacity,allocation,physical list: %s" % blkdata)
    else:
        return 1
                
    if check_block_data(blockdev, blkdata, logger):
        logger.error("checking domblkinfo data FAILED")
        return 1
    else:
        logger.info("checking domblkinfo data SUCCEEDED")
        
    return 0
             
     
 
     

    
  
   
     















   
