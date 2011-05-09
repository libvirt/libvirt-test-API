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
# Summary: class nwfilterTest.
# Description: nwfilter operation.
# Maintainer: Guannan Ren <gren@redhat.com>
# Updated: May Thu 6, 2010
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

class nwfilterAPI(object):
    def __init__(self, connection):
        self.conn = connection

    def get_list(self):
        try:
            return self.conn.listNWFilters()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_numbers(self):
        try:
            return self.conn.numOfNWFilters()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def define(self, nwfilterxmldesc):
        try:
            return self.conn.nwfilterDefineXML(nwfilterxmldesc)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_nwfilter_obj(self, name):
        try:
            return self.conn.nwfilterLookupByName(name)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def lookup_by_UUIDString(self, UUIDString):
        try:
            obj = self.conn.nwfilterLookupByUUIDString(UUIDString)
            return obj.name()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_uuid(self, name):
        try:
            obj = self.get_nwfilter_obj(name)
            uuid = obj.UUID()
            return repr(uuid)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_uuid_string(self, name):
        try:
            obj = self.get_nwfilter_obj(name)
            return obj.UUIDString()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def xmldesc_dump(self, name):
        try:
            obj = self.get_nwfilter_obj(name)
            return obj.XMLDesc(0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_connect(self, name):
        try:
            obj = self.get_nwfilter_obj(name)
            conn = obj.connect()
            return conn.getURI()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def undefine(self, name):
        try:
            obj = self.get_nwfilter_obj(name)
            return obj.undefine()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

