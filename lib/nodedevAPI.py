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
# Summary: Class NodedevTest.
# Description: Node Device function modules.
# Maintainer: Neil Zhang <nzhang@redhat.com>
# updated: Thu Jul 23, 2009
# Version: 0.1.0

import os
import sys
import re

import libvirt

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

class NodedevAPI:
    def __init__(self, connection):
        self.conn = connection.get_conn()

    def create(self, device_xml):
        try:
            obj = self.conn.nodeDeviceCreateXML(device_xml, 0)
            return obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def lookup_by_name(self, name):
        try:
            obj = self.conn.nodeDeviceLookupByName(name)
            return obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_number(self, cap):
        try:
            num = self.conn.numOfDevices(cap, 0)
            return num
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_info(self):
        try:
            node_info = self.conn.getInfo()
            return node_info
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def lists(self, cap):
        try:
            devices_list = self.conn.listDevices(cap, 0)
            return devices_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    #
    # virNodeDevice functions
    #

    def dumpxml(self, name):
        try:
            obj = self.lookup_by_name(name)
            xmldesc = obj.XMLDesc(0)
            return xmldesc
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def destroy(self, name):
        try:
            obj = self.lookup_by_name(name)
            obj.destroy()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def dettach(self, name):
        try:
            obj = self.lookup_by_name(name)
            obj.dettach()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def reattach(self, name):
        try:
            obj = self.lookup_by_name(name)
            obj.reAttach()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def reset(self, name):
        try:
            obj = self.lookup_by_name(name)
            obj.reset()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_name(self, obj):
        try:
            device_name = obj.name()
            return device_name
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_num_of_caps(self, name):
        try:
            obj = self.lookup_by_name(name)
            device_numofcaps = obj.numOfCaps()
            return device_numofcaps
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_parent(self, name):
        try:
            obj = self.lookup_by_name(name)
            device_parent = obj.parent()
            return device_parent
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def list_caps(self, name):
        try:
            obj = self.lookup_by_name(name)
            caps_list = obj.listCaps()
            return caps_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def connect(self, name):
        try:
            obj = self.lookup_by_name(name)
            return obj.connect()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

