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
# Summary: class connect.
# Description: connection operation.
# Maintainer: Alex Jia <ajia@redhat.com>
# Updated: Tue Sep 15, 2009
# Version: 0.1.0

import sys
import os
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

class ConnectAPI(object):
    def __init__(self, uri):
        self.uri = uri
        self.conn = None

    def open(self):
        try:
            self.conn = libvirt.open(self.uri)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def open_read_only(self):
        try:
            self.conn = libvirt.openReadOnly(self.uri)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def openAuth(self, auth, flags = 0):
        try:
            self.conn = libvirt.openAuth(self.uri, auth, flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_conn(self):
        return self.conn

    def get_caps(self):
        try:
            caps = self.conn.getCapabilities()
            return caps
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_free_memory(self):
        try:
            freemem = self.conn.getFreeMemory()
            return freemem
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_host_name(self):
        try:
            hostname = self.conn.getHostname()
            return hostname
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_max_vcpus(self, type):
        try:
            maxvcpu = self.conn.getMaxVcpus(type)
            return maxvcpu
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_type(self):
        try:
            type = self.conn.getType()
            return type
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_uri(self):
        try:
            uri = self.conn.getURI()
            return uri
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def ref(self,  uri):
        try:
            refer = self.conn.ref()
            return refer
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_cells_free_memory(self, startCell, maxCells):
        try:
            cfreemem = self.conn.getCellsFreeMemory(startCell, maxCells)
            return cfreemem
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_info(self):
        try:
            info = self.conn.getInfo()
            return info
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def baseline_cpu(self, xmlCPUs, flag = 0):
        try:
            return self.conn.baselineCPU(xmlCPUs, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def compare_cpu(self, xmlDesc, flag = 0):
        try:
            return self.conn.compareCPU(xmlDesc, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_version(self):
        try:
            return self.conn.getVersion()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_lib_version(self):
        try:
            return self.conn.getLibVersion()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain_XML_from_native(self, nativeFormat, nativeConfig, flag = 0):
        try:
            return self.conn.domainXMLFromNative(nativeFormat,
                                                 nativeConfig,
                                                 flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain_XML_to_native(self, nativeFormat, domainXml, flag = 0):
        try:
            return self.conn.domainXMLToNative(nativeFormat, domainXml, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def find_storage_pool_source(self, type, srcSpec, flag = 0):
        try:
            return self.conn.findStoragePoolSources(type, srcSpec, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def isEncrypted(self):
        try:
            return self.conn.isEncrypted()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def isSecure(self):
        try:
            return self.conn.isSecure()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def newStream(self, flag = 0):
        try:
            return self.conn.newStream(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_last_error(self):
        try:
            return self.conn.virConnGetLastError()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def reset_last_error(self):
        try:
            return self.conn.virConnResetLastError()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain_event_deregister(self, cb):
        try:
            return self.conn.domainEventDeregister(cb)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain_event_deregister_any(self, callbackID):
        try:
            return self.conn.domainEventDeregisterAny(callbackID)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain_event_register(self, cb, opaque):
        try:
            return self.conn.domainEventRegister(cb, opaque)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def domain_event_register_any(self, dom, eventID, cb, opaque):
        try:
            return self.conn.domainEventRegisterAny(dom, eventID, cb, opaque)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def close(self):
        try:
            if self.conn:
                return self.conn.close()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def createLinux(self, xmlDesc, flags):
        try:
            return self.conn.createLinux(self, xmlDesc, flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def lookupByUUID(self, uuid):
        try:
            return self.conn.lookupByUUID(self, uuid)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def migrate(self, domain, flags, dname, uri, bandwidth):
        try:
            return self.migrate(self, domain, flags, dname, uri, bandwidth)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def networkLookupByUUID(self, uuid):
        try:
            return self.networkLookupByUUID(self, uuid)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def numOfDefinedDomains(self):
        try:
            return self.numOfDefinedDomains(self)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def numOfDomains(self):
        try:
            return self.numOfDomains(self)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def nwfilterLookupByUUID(self, uuid):
        try:
            return self.nwfilterLookupByUUID(self, uuid)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

VIR_CRED_AUTHNAME = libvirt.VIR_CRED_AUTHNAME
VIR_CRED_PASSPHRASE = libvirt.VIR_CRED_PASSPHRASE

