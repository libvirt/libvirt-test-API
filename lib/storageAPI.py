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
# Summary: class StorageAPI.
# Description: storage operation.
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

# virStoragePoolState
VIR_STORAGE_POOL_INACTIVE = 0
VIR_STORAGE_POOL_BUILDING = 1
VIR_STORAGE_POOL_RUNNING = 2
VIR_STORAGE_POOL_DEGRADED = 3

class StorageAPI(object):
    def __init__(self, connection):
        self.conn = connection 

    def define_pool(self, storage_xml):
        try:
            self.conn.storagePoolDefineXML(storage_xml, 0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def create_pool(self, storage_xml):
        try:
            self.conn.storagePoolCreateXML(storage_xml, 0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_number_of_defpools(self):
        defpool_num = None
        try:
            defpool_num = self.conn.numOfDefinedStoragePools()
            return defpool_num
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_number_of_pools(self):
        pool_num = None
        try:
            pool_num = self.conn.numOfStoragePools()
            return pool_num
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def defstorage_pool_list(self):
        defpool_list = []
        try:
            defpool_list = self.conn.listDefinedStoragePools()
            return defpool_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
    
    def storage_pool_list(self):
        pool_list = []
        try:
            pool_list = self.conn.listStoragePools()
            return pool_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
 
    def pool_lookupby_uuid(self, pooluuid):
        poolname = None
        try:
            poolobj = self.conn.storagePoolLookupByUUID(pooluuid)
            poolname = poolobj.name()
            return poolname
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def pool_lookupby_uuidstring(self, pooluuidstring):
        poolname = None
        try:
            poolobj = self.conn.storagePoolLookupByUUIDString(pooluuidstring)
            poolname = poolobj.name()
            return poolname
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def volume_lookupby_key(self, volkey):
        volname = None
        try:
            volobj = self.conn.storageVolLookupByKey(volkey)
            volname = volobj.name()
            return volname
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def volume_lookupby_path(self, volpath):
        volname = None
        try:
            volobj = self.conn.storageVolLookupByPath(volpath)
            volname = volobj.name()
            return volname
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
           
    def get_pool_obj(self, poolname):
        poolobj = None
        try:
            poolobj = self.conn.storagePoolLookupByName(poolname)
            return poolobj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_pool_uuid(self, poolname):
        uuidstr = None
        try:
            poolobj = self.get_pool_obj(poolname)
            uuidstr = poolobj.UUID()
            return repr(uuidstr) 
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_pool_uuidstring(self, poolname):
        uuidstr = None
        try:
            poolobj = self.get_pool_obj(poolname)
            uuidstr = poolobj.UUIDString()
            return uuidstr
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_pool_state(self, poolname):
        state = ''
        try:
            stg_pool_info = self.get_pool_info(poolname)
            state = stg_pool_info[0]
            if state == VIR_STORAGE_POOL_INACTIVE:
                state = 'inactive'
            elif state == VIR_STORAGE_POOL_BUILDING:
                state = 'building' 
            elif state == VIR_STORAGE_POOL_RUNNING:
                state = 'running' 
            elif state == VIR_STORAGE_POOL_DEGRADED:
                state = 'degraded' 
            else :
                state = 'unknown'
            return state
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)       

    def get_pool_info(self, poolname):
        pool_info = []
        try:
            poolobj = self.get_pool_obj(poolname)
            pool_info = poolobj.info()
            return pool_info
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)       
 
    def dump_pool(self, poolname, flags = 0):
        xmldump = None
        try:
            poolobj = self.get_pool_obj(poolname)
            xmldump = poolobj.XMLDesc(flags)
            return xmldump 
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def active_pool(self, poolname, flags = 0):
        try: 
            poolobj = self.get_pool_obj(poolname)
            return poolobj.create(flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
               
    def delete_pool(self, poolname, flags = 1):
        try:
            pool_obj = self.get_pool_obj(poolname)
            return pool_obj.delete(flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
            
    def set_pool_autostart(self, poolname, switch):
        try:
            poolobj = self.get_pool_obj(poolname)
            if switch == 'on':
                return poolobj.setAutostart(1)
            elif switch == 'off':
                return poolobj.setAutostart(0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_pool_autostart(self, poolname):
        autostatus = None
        try:
            poolobj = self.get_pool_obj(poolname)
            ret = poolobj.autostart()
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
            
    def refresh_pool(self, poolname, flags = 0):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.refresh(flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def build_pool(self, poolname, flags = 0):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.build(flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
    
    def destroy_pool(self, poolname):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.destroy()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
                     
    def undefine_pool(self, poolname):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.undefine()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
 
    def vol_create_from(self, poolname, volname, xmldesc, flags = 0):
        try:
            poolobj = self.get_pool_obj(poolname)
            volobj = self.get_volume_obj(poolname, volname)
            return poolobj.createXMLFrom(xmldesc, volobj, flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
 
    def isActive_pool(self, poolname):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.isActive()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def isPersistent_pool(self, poolname):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.isPersistent()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
 
    def volume_wipe(self, poolname, volname, flags = 0):
        try:
            volobj = self.get_volume_obj(poolname, volname)
            return volobj.wipe(flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def create_volume(self, poolname, vol_xml_desc):
        try:
            poolobj = self.get_pool_obj(poolname)
            return poolobj.createXML(vol_xml_desc, 0)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_volume_list(self, poolname):
        vollist = []
        try:
            poolobj = self.get_pool_obj(poolname)
            vollist = poolobj.listVolumes()
            return vollist 
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_volume_number(self, poolname):
        volum = None
        try:    
            poolobj = self.get_pool_obj(poolname)
            volnum = poolobj.numOfVolumes()
            return volnum
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
                
    def get_volume_obj(self, poolname, volname):
        volobj = None
        try:
            poolobj = self.get_pool_obj(poolname)
            volobj = poolobj.storageVolLookupByName(volname)
            return volobj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_volume_info(self, poolname, volname):
        vol_info = []
        try:
            volobj = self.get_volume_obj(poolname, volname)
            vol_info = volobj.info()
            return vol_info
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
 
    def get_volume_key(self, poolname, volname):
        vol_key = None
        try:
            volobj = self.get_volume_obj(poolname, volname)
            vol_key = volobj.key()
            return vol_key
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_volume_path(self, poolname, volname):
        vol_path = None
        try:
            volobj = self.get_volume_obj(poolname, volname)
            vol_path = volobj.path()
            return vol_path
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def delete_volume(self, poolname, volname, flags = 0):
        try:
            volobj = self.get_volume_obj(poolname, volname)
            return volobj.delete(flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def pool_lookupby_volume(self, poolname, volume):
        pool = None
        try:
            volobj = self.get_volume_obj(poolname, volume)
            poolobj = volobj.storagePoolLookupByVolume()
            pool = poolobj.name()
            return pool
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def dump_volume(self, poolname, volname):
        volxml = None
        try:
            volobj = self.get_volume_obj(poolname, volname)
            volxml = volobj.XMLDesc(0)
            return volxml
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_pool_connect(self, pooluuidstring):
        try:
            pool_obj = self.conn.storagePoolLookupByUUIDString(pooluuidstring)
            return pool_obj.connect()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_vol_connect(self, poolname, volname):  
        try:
            volobj = self.get_volume_obj(poolname, volname)
            return volobj.connect()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

