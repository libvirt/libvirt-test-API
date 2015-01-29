#!/usr/bin/env python
#test DHCPLeases() API for libvirt

import os
import time
import libvirt
from libvirt import libvirtError
from utils import utils
from src import sharedmod

required_params = ('networkname',)
optional_params = {'macaddr': ''}

LEASE_FILE = "/var/lib/libvirt/dnsmasq/"

def check_ip(ipaddr, logger):
    """
       return a string according to ip address type, return 'ipv4' for ipv4,
       return 'ipv6' for ipv6, return False for others
    """
    addr4 = ipaddr.strip().split('.')
    addr6 = ipaddr.strip().split(':')
    if len(addr4) == 4:
        iptype = "ipv4"
    elif len(addr6) == 6:
        iptype = "ipv6"
    else:
        return False
    return iptype

def get_network_type(ipaddr,logger):
    """
       return 0 or 1 for ipv4/ipv6, this function will be used in
       check_ipv4_values()/check_ipv6_values()
    """
    if check_ip(ipaddr, logger) == "ipv4":
        return 0
    elif check_ip(ipaddr, logger) == "ipv6":
        return 1

def get_bridge_name(network,logger):
    """
       get bridge name under specified network from specified network conf
    """
    CONF_NETWORK = LEASE_FILE + network + ".conf"
    GREP_BRIDGE = "grep \"^interface=\" %s | awk -F\"=\" '{print $2}'"
    status, output = utils.exec_cmd(GREP_BRIDGE % CONF_NETWORK, shell=True)
    if not status:
        pass
    else:
        logger.error("\"" + GREP_BRIDGE + "\"" + "error")
        logger.error(output)
        return False
    return output[0]

def get_ip_prefix(network, iptype, logger):
    """
       get ip prefix according to IP type
    """
    br = get_bridge_name(network, logger)
    PREFIX = "ip -4 -o ad show %s | awk '{print $4}'|awk -F\"/\" '{print $2}'"
    PREFIX_6 = "ip -6 -o ad show %s|awk '{print $4}'|awk -F\"/\" '{print $2}'"
    if iptype == "ipv4":
        status, output = utils.exec_cmd(PREFIX % br, shell=True)
    elif iptype == "ipv6":
        status, output = utils.exec_cmd(PREFIX_6 % br, shell=True)
    if not status:
        pass
    else:
        logger.error("\"" + GREP_BRIDGE + "\"" + "error")
        logger.error(output)
        return False
    return output[0]

def get_info_from_dnsmasq(network,macaddr,logger):
    """
       generate dict for lease info from virtual network's lease file
    """
    title = ['expirytime','mac','ipaddr','hostname','clientid']
    output_list = []
    lease_dnsmasq = []
    temp = []
    remove_list = []
    GREP_MAC = "grep -w %s" + " " + LEASE_FILE_DNSMASQ
    CAT_FILE = "cat" + " " + LEASE_FILE_DNSMASQ

    status, output = utils.exec_cmd(CAT_FILE, shell=True)
    if not status:
        for i in range(0, len(output)):
            output_list = []
            output_str = output[i]
            for item in output_str.split(" "):
                output_list.append(item)
            lease_dnsmasq.append(dict(zip(title,output_list)))

        #due to no mac field in IPv6 line, so do nothing here temporarily.
        if macaddr != None:
             pass

        #remove bridge duid line
        for i in range(0, len(lease_dnsmasq)):
            if lease_dnsmasq[i]['expirytime'] == 'duid':
                remove_list.append(lease_dnsmasq[i])

        for i in range(0, len(remove_list)):
                lease_dnsmasq.remove(remove_list[i])

        #remove expiry leases
        for i in range(0, len(lease_dnsmasq)):
            temp = int(lease_dnsmasq[i]['expirytime'])
            lease_dnsmasq[i]['expirytime'] = temp

        remove_list = []
        for i in range(0, len(lease_dnsmasq)):
            if time.time() >= int(lease_dnsmasq[i]['expirytime']):
                remove_list.append(lease_dnsmasq[i])

        for i in range(0, len(remove_list)):
                lease_dnsmasq.remove(remove_list[i])

        #replace * to None
        for i in range(0, len(lease_dnsmasq)):
            if lease_dnsmasq[i]['hostname'] == "*":
                lease_dnsmasq[i]['hostname'] = None
            if lease_dnsmasq[i]['clientid'] == "*":
                lease_dnsmasq[i]['clientid'] = None

        return lease_dnsmasq
    else:
        logger.error("\"" + CAT_FILE + "\"" + "error")
        logger.error(output)
        return False

def compare_values(op1, op2, network, iptype, logger):
    """
       check all printed values from API
    """
    dnsmasq = op1
    api = op2
    temp = int(api['expirytime'])
    api['expirytime'] = temp

    for j in range(0,len(dnsmasq)):
        if dnsmasq[j]['hostname'] == api['hostname'] and \
           dnsmasq[j]['expirytime'] == api['expirytime']:
            if dnsmasq[j]['ipaddr'] == api['ipaddr'] and \
               dnsmasq[j]['clientid'] == api['clientid']:

                if iptype == "ipv4":
                    logger.debug("PASS: hostname:%s expirytime:%s ipaddr:%s" \
                           % (api['hostname'],api['expirytime'],api['ipaddr']))
                    logger.debug("Unsupported: clientid: %s in IPv4" \
                            % (api['clientid']))
                elif iptype == "ipv6":
                    logger.debug("PASS: hostname: %s expirytime: %s ipaddr: %s \
clientid: %s" % (api['hostname'],api['expirytime'],api['ipaddr'],\
api['clientid']))

                if iptype == "ipv4" and api['mac'] == dnsmasq[j]['mac']:
                    logger.debug("PASS: mac: %s" % api['mac'])
                elif iptype == "ipv6" and api['iaid'] == dnsmasq[j]['mac']:
                    logger.debug("PASS: iaid: %s" % api['iaid'])
                else:
                    logger.error("Fail: mac/iaid: %s/%s" % (api['mac'], \
                                 api['iaid']))
                    return False

                break
            else:
                if j == len(dnsmasq) - 1:
                    logger.debug("Last loop %d, FAIL: %s" % (j,api))
                    logger.debug("failed on ipaddr or clientid")
                    return False
                else:
                    logger.debug("Skipped loop %d,Warning: ipaddr: %s \
clientid: %s" % (j,api['ipaddr'],api['clientid']))
                    continue
        else:
            if j == len(dnsmasq) - 1:
                logger.error("Fail: hostname: %s expirytime: %s ipaddr: %s \
clientid: %s"  % (api['hostname'],api['expirytime'],api['ipaddr'], \
api['clientid']))
                logger.error("Last loop %d, FAIL: %s" % (j,api))
                return False
            else:
                logger.debug("Skipped loop %d,Warning: hostname: \
%s expirytime: %s" % (j,api['hostname'],api['expirytime']))
                continue
    if not api['iface'] == get_bridge_name(network,logger):
        logger.error("FAIL: iface: %s" % api['iface'])
        return False
    else:
        logger.debug("PASS: iface: %s" % api['iface'])
    if not api['type'] == get_network_type(api['ipaddr'],logger):
        logger.error("FAIL: type: %s" % api['type'])
        return False
    else:
        logger.debug("PASS: type: %s" % api['type'])

    if not api['prefix'] == int(get_ip_prefix(network, iptype ,logger)):
        logger.error("FAIL: prefix: %s" % api['prefix'])
        logger.error("FAIL: %s" % api)
        return False
    else:
        logger.debug("PASS: prefix: %s" % api['prefix'])
    if iptype == "ipv4":
        if not api['iaid'] == None:
            logger.error("FAIL: iaid: %s" % api['iaid'])
            return False
        else:
            logger.debug("Unsupported: iaid: %s in IPv4" % api['iaid'])
            logger.debug("PASS: %s" % api)
    elif iptype == "ipv6":
         logger.debug("Ignoring mac checking on IPv6 line %s" % api['mac'])
         logger.debug("PASS: %s" % api)

    return True

def check_values(op1, op2, network, logger):
     """
        check each line accorting to ip type, if ipv4 go to check_ipv4_values
        if ipv6, go to check_ipv6_values.
     """
     networkname = network
     dnsmasq = op1
     api = op2

     for i in range(0, len(api)):
         if check_ip(api[i]['ipaddr'],logger) == "ipv4":
             if not compare_values(dnsmasq,api[i],networkname,"ipv4",logger):
                 return False
         elif check_ip(api[i]['ipaddr'],logger) == "ipv6":
             if not compare_values(dnsmasq,api[i],networkname,"ipv6",logger):
                 return False
         else:
             logger.error("invalid list element for ipv4 and ipv6")
             return False
     return True

def network_dhcp_leases(params):
    """
       test API for DHCPLeases in class virNetwork
    """
    global LEASE_FILE_DNSMASQ
    logger = params['logger']
    networkname = params['networkname']
    LEASE_FILE_DNSMASQ = "/var/lib/libvirt/dnsmasq/" + networkname + ".leases"
    mac_value = params.get('macaddr', None)
    conn = sharedmod.libvirtobj['conn']
    logger.info("The given mac is %s" % (mac_value))

    if not os.path.exists(LEASE_FILE_DNSMASQ):
        logger.error("leases file for %s is not exist" % networkname)
        logger.error("%s" % LEASE_FILE_DNSMASQ)
        return 1
    dhcp_lease_dns = get_info_from_dnsmasq(networkname, mac_value, logger)
    logger.info("From dnsmasq: %s" % (dhcp_lease_dns))
    if not dhcp_lease_dns:
        return 1

    netobj = conn.networkLookupByName(networkname)

    try:
        dhcp_lease_api = netobj.DHCPLeases(mac_value,0)
        if not dhcp_lease_api and dhcp_lease_dns:
            logger.info("From API: %s" % (dhcp_lease_api))
            return 1
        logger.info("From API: %s" % (dhcp_lease_api))
        if not check_values(dhcp_lease_dns,dhcp_lease_api,networkname,logger):
           return 1

    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    return 0
