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

# InterfaceState
VIR_INTERFACE_INACTIVE = 0
VIR_INTERFACE_RUNNING = 1
VIR_INTERFACE_ERROR = -1

class InterfaceAPI(object):
    def __init__(self, connection):
        self.conn = connection.get_conn()

    def get_active_list(self):
        try:
            active_list = self.conn.listInterfaces()
            return active_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_defined_list(self):
        try:
            define_list = self.conn.listDefinedInterfaces()
            return define_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_active_number(self):
        try:
            active_number = self.conn.numOfInterfaces()
            return active_number
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_defined_number(self):
        try:
            defined_number = self.conn.numOfDefinedInterfaces()
            return defined_number
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_iface_by_name(self, name):
        try:
            iface_obj = self.conn.interfaceLookupByName(name)
            return iface_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_iface_by_mac_string(self, macstr):
        try:
            iface_obj = self.conn.interfaceLookupByMACString(macstr)
            return iface_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_name(self, macstr):
        try:
            iface_obj = self.get_iface_by_mac_string(macstr)
            name = iface_obj.name()
            return name
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_mac_string(self, name):
        try:
            iface_obj = self.get_iface_by_name(name)
            mac_str = iface_obj.MACString()
            return mac_str
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_xml_desc(self, name):
        try:
            iface_obj = self.get_iface_by_name(name)
            iface_xml = iface_obj.XMLDesc(0)
            return iface_xml
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_state(self, name):
        try:
            iface_obj = self.get_iface_by_name(name)
            retval = iface_obj.isActive()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def define(self, xml_desc):
        try:
            retval = self.conn.interfaceDefineXML(xml_desc, 0)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def undefine(self, name):
        try:
            def_list = self.get_defined_list()
            iface_obj = self.get_iface_by_name(name)
            if name in def_list:
                retval = iface_obj.undefine()
                return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def create(self, name, flags = 0):
        try:
            iface_obj = self.get_iface_by_name(name)
            retval = iface_obj.create(flags)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def destroy(self, name, flags = 0):
        try:
            iface_obj = self.get_iface_by_name(name)
            retval = iface_obj.destroy(flags)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def connect(self, name):
        try:
            iface_obj = self.get_iface_by_name(name)
            retval = iface_obj.connect()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

