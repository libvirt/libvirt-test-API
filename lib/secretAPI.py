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
# Summary: class SecretAPI.
# Description: secret operation.
# Maintainer: Alex Jia <ajia@redhat.com>
# Updated: Thu May 6, 2010
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

class SecretAPI(object):
    def __init__(self, connection):
        self.conn = connection

    def get_defined_list(self):
        try:
            return self.conn.listSecrets()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def get_defined_number(self):
        try:
            return self.conn.numOfSecrets()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      
    
    def get_secret_by_uuid(self, uuid):
        try:
            return self.conn.secretLookupByUUID(uuid)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      
        
    def get_secret_by_uuid_string(self, uuidstr):
        try:
            return self.conn.secretLookupByUUIDString(uuidstr)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def get_secret_by_usage(self, usageType, usageID):
        try:
            return self.conn.secretLookupByUsage(usageType, usageID)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      
        
    def get_uuid(self, uuidstr):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.uuid()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def get_uuid_string(self, usageType, usageID):
        try:
            secret_obj = self.get_secret_by_usage(usageType, usageID)
            return secret_obj.UUIDString()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def get_xml_desc(self, uuidstr):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.XMLDesc(0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      
    
    def get_usage_id(self, uuidstr):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.usageID()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      
    
    def get_usage_type(self, uuidstr):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.usageType()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def set_value(self, uuidstr, flag = 0):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.setValue(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def get_value(self, flag = 0):
        """can get value if and only if private value is yes"""
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.value(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      

    def define(self, xml_desc, flag = 0):
        try:
            return self.conn.secretDefineXML(xml_desc, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)      
           
    def undefine(self, uuidstr):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.undefine()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)     

    def connect(self, uuidstr):
        try:
            secret_obj = self.get_secret_by_uuid_string(uuidstr)
            return secret_obj.connect()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
         
