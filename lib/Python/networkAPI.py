#!/usr/bin/env python
#
# libvirt-test-API is copyright 2010 Red Hat, Inc.
#
# libvirt-test-API is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
#
# Summary: class InterfaceAPI.
# Description: interface operation.
# Maintainer: Alex Jia <ajia@redhat.com>
# Updated: Mon Apr 12, 2010
# Version: 0.1.0

import sys 
import libvirt
import re
import os

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)
    
pwd = os.getcwd() 
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

import exception

class NetworkAPI(object):
    def __init__(self, connection):
        self.conn = connection     

    def define(self, netxmldesc):
        try:
            return self.conn.networkDefineXML(netxmldesc)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def create(self, netxmldesc):
        try:
            return self.conn.networkCreateXML(netxmldesc)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def defined_list(self):
        try:
            return self.conn.listDefinedNetworks()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)            

    def network_list(self):
        try:
            return self.conn.listNetworks()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_define_number(self):
        try:
            return  self.conn.numOfDefinedNetworks()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)            

    def get_number(self):
        try:
            return self.conn.numOfNetworks()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
            

    def netwok_lookupby_UUIDString(UUIDString):
        try:
            netobj = self.conn.networkLookupByUUIDString(UUIDString)
            return netobj.name()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_net_obj(self, netname):
        try:
            return self.conn.networkLookupByName(netname)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)        

    def get_connect(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            conn = netobj.connect()
            return conn.getURI()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)            
 
    def get_uuid(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            uuid = netobj.UUID()
            return  repr(uuid)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)            
    
    def get_uuid_string(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            return netobj.UUIDString()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
    
    def get_ref(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            return netobj.ref()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)          
        
    def get_bridge_name(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            return netobj.bridgeName()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def netxml_dump(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            return netobj.XMLDesc(0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)        

    def undefine(self, netname):
        try:
            netobj = self.get_net_obj(netname)
            return netobj.undefine()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def destroy(self, netname):
        try: 
            netobj = self.get_net_obj(netname)
            return netobj.destroy()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def start(self, netname):
        try: 
            netobj = self.get_net_obj(netname)
            return netobj.create()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def setnetAutostart(self, netname, switch):
        try:
            netobj = self.get_net_obj(netname)
            return netobj.setAutostart(switch)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
 
    def get_autostart(self, netname):  
        autostatus = None
        try:
            netobj = self.get_net_obj(netname)
            ret = netobj.autostart()
            if ret == 0:
                autostatus = 'off'
                return autostatus
            elif ret == 1:
                autostatus = 'on'
                return autostatus
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def isActive(self, netname):
        try: 
            netobj = self.get_net_obj(netname)
            return netobj.isActive()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def isPersistent(self, netname):
        try: 
            netobj = self.get_net_obj(netname)
            return netobj.isPersistent()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

