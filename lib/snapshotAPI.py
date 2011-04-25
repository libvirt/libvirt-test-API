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
# Summary: class SnapshotTest.
# Description: snapshot operation.
# Maintainer: Alex Jia <ajia@redhat.com>
# Updated: Fri May 14, 2010
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

class SnapshotAPI(object):
    def __init__(self, connection):
        self.conn = connection     

    def create(self, domname, xml_desc, flag = 0):
	try:
            dom_obj = self.conn.lookupByName(domname)
            return dom_obj.snapshotCreateXML(xml_desc, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_snapshot_current(self, domname, flag = 0):
        try:
            dom_obj = self.conn.lookupByName(domname)
            return dom_obj.snapshotCurrent(flag).getXMLDesc(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)        

    def snapshot_name_list(self, domname, flag = 0):
        try:
            dom_obj = self.conn.lookupByName(domname)
            return dom_obj.snapshotListNames(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code) 

    def snapshot_nums(self, domname, flag = 0):
        try:
            dom_obj = self.conn.lookupByName(domname)
            return dom_obj.snapshotNum()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def snapshot_lookup_by_name(self, domname, snapname, flag = 0):
        try:
            dom_obj = self.conn.lookupByName(domname)
            return dom_obj.snapshotLookupByName(snapname, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def revertToSnapshot(self, domname, snapname, flag = 0):
        try:
            dom_obj = self.conn.lookupByName(domname)
            snap = self.snapshot_lookup_by_name(domname, snapname)
            return  dom_obj.revertToSnapshot(snap, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
            
    def delete(self, domname, snapname, flag = 0):
        try:
            snap = self.snapshot_lookup_by_name(domname, snapname, flag = 0)
            return snap.delete(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)            

    def get_xml_desc(self, domname, snapname, flag = 0):
        try:
            snap = self.snapshot_lookup_by_name(domname, snapname, flag = 0)
            return snap.getXMLDesc(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain(self, domname):
        try:
            snap = self.snapshot_lookup_by_name(domname, snapname, flag = 0)
            return  snap.domain()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
  
