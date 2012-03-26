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
# Summary: class DomainTest.
# Description: domain operation.
# Maintainer: Alex Jia <ajia@redhat.com>
# Updated: Dec Wed 23, 2009
# Version: 0.1.0

import sys
import libxml2
import commands
import re
import os

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

class DomainAPI(object):
    def __init__(self, connection):
        self.conn = connection.get_conn()

    def get_list(self):
        dom_list = []
        try:
            ids = self.conn.listDomainsID()
            for id in ids:
                obj = self.conn.lookupByID(id)
                dom_list.append(obj.name())
            return dom_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_domain_by_name(self, name):
        try:
            dom_obj = self.conn.lookupByName(name)
            return dom_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_domain_by_id(self, id):
        try:
            id_list = self.conn.listDomainsID()
            dom_obj = self.conn.lookupByID(id)
            return dom_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_domain_by_uuid_string(self, uuidstr):
        try:
            dom_obj = self.conn.lookupByUUIDString(uuidstr)
            return dom_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_id(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            id = dom_obj.ID()
            return id
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_name(self, id):
        try:
            dom_obj = self.get_domain_by_id(id)
            name = dom_obj.name()
            return name
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_defined_list(self):
        try:
            def_list = self.conn.listDefinedDomains()
            return def_list
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_defined_obj(self, domname):
        try:
            def_dom_list = self.conn.listDefinedDomains()
            def_dom_obj = self.conn.lookupByName(domname)
            return def_dom_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_xml_desc(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            dom_xml = dom_obj.XMLDesc(0)
            return dom_xml
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def create(self, dom_xml_desc, flags = 0):
        try:
            dom_obj = self.conn.createXML(dom_xml_desc, flags)
            return dom_obj
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def define(self, dom_xml_desc):
        try:
            self.conn.defineXML(dom_xml_desc)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def undefine(self, domname):
        try:
            dom_obj = self.get_defined_obj(domname)
            dom_obj.undefine()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def start(self, domname):
        try:
            dom_obj = self.get_defined_obj(domname)
            retval = dom_obj.create()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def start_with_flags(self, domname, flags = 0):
        try:
            dom_obj = self.get_defined_obj(domname)
            retval = dom_obj.createWithFlags(flags)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def suspend(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.suspend()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def resume(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.resume()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def save(self, domname, to):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.save(to)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)


    def restore(self, domname, frm):
        try:
            sys.stdout.flush()
            retval = self.conn.restore(frm)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def migrate(self, domname, dconn, flags, dname = None, uri = None, bandwidth = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.migrate(dconn, flags, dname, uri, 0)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def reboot(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.reboot(0)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def destroy(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.destroy()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def shutdown(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.shutdown()
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_info(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            info = dom_obj.info()
            return info
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_auto_start(self, domname):
        try:
            dom_obj = self.conn.lookupByName(domname)
            flag = dom_obj.autostart()
            if flag == 1:
                flag = 'enable'
            elif flag == 0:
                flag = 'disable'
            return flag
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_auto_start(self, domname, flag = 0):
        try:
            dom_obj = self.conn.lookupByName(domname)
            retval = dom_obj.setAutostart(flag)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_os_type(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            os_type = dom_obj.OSType()
            return os_type
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def attach_device(self, domname, xml_desc):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.attachDevice(xml_desc)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def detach_device(self, domname, xml_desc):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.detachDevice(xml_desc)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_connect(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            conn = dom_obj.connect()
            return conn
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_ref(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            ref = dom_obj.ref()
            return ref
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_vcpus(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            vcpu_info = dom_obj.vcpus()
            return vcpu_info
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_pin_vcpu(self, domname, vcpu, cpumap):
        try:
            dom_obj = self.get_domain_by_name(domname)
            pin_vcpu = dom_obj.pinVcpu(vcpu, cpumap)
            return pin_vcpu
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_uuid(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            uuid = dom_obj.UUID()
            return uuid
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_uuid_string(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            uuid_string = dom_obj.UUIDString()
            return uuid_string
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_max_memory(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            max_memory = dom_obj.maxMemory()
            return max_memory
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_max_vcpus(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            max_vcpus = dom_obj.maxVcpus()
            return max_vcpus
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_max_memory(self, domname, memory):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.setMaxMemory(memory)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_block_stats(self, domname):
        try:
            dom = self.get_domain_by_name(domname)
            xml = dom.XMLDesc(0)
            doc = libxml2.parseDoc(xml)
            cont = doc.xpathNewContext()
            devs = cont.xpathEval("/domain/devices/disk/target/@dev")
            path = devs[0].content
            blkstats = dom.blockStats(path)
            return (blkstats, path)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_interface_stats(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            xml = dom_obj.XMLDesc(0)
            doc = libxml2.parseDoc(xml)
            ctx = doc.xpathNewContext()
            devs = ctx.xpathEval("/domain/devices/interface/target/@dev")
            path = devs[0].content
            ifstats = dom_obj.interfaceStats(path)
            return (ifstats, path)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_memory(self, domname, memory):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.setMemory(memory)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_vcpus(self, domname, nvcpus):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.setVcpus(nvcpus)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_memory(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            strs = commands.getoutput('virsh dominfo %s' %domname)
            memory = strs.split('\n')[9]
            return memory
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_state(self, domname):
        dom_state = ''
        try:
            dom_obj = self.get_domain_by_name(domname)
            state = dom_obj.info()
            if state[0] == VIR_DOMAIN_NOSTATE:
                dom_state = 'nostate'
            elif state[0] == VIR_DOMAIN_RUNNING:
                dom_state = 'running'
            elif state[0] == VIR_DOMAIN_BLOCKED:
                dom_state = 'blocked'
            elif state[0] == VIR_DOMAIN_PAUSED:
                dom_state = 'paused'
            elif state[0] == VIR_DOMAIN_SHUTDOWN:
                dom_state = 'shutdown'
            elif state[0] == VIR_DOMAIN_SHUTOFF:
                dom_state = 'shutoff'
            elif state[0] == VIR_DOMAIN_CRASHED:
                dom_state = 'crashed'
            else:
                dom_state = 'dying'
            return dom_state
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_sched_type(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            sched_type = dom_obj.schedulerType()
            return sched_type
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_sched_params(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            sched_params = dom_obj.schedulerParameters()
            return sched_params
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_sched_params_flags(self, domname, flags):
        try:
            dom_obj = self.get_domain_by_name(domname)
            sched_params_flags = dom_obj.schedulerParametersFlags(flags)
            return sched_params_flags
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_sched_params(self, domname, params):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.setSchedulerParameters(params)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_sched_params_flags(self, domname, params, flags):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.setSchedulerParametersFlags(params, flags)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def core_dump(self, domname, to, flags = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            retval = dom_obj.coreDump(to, flags)
            return retval
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def block_info(self, domname, path, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockInfo(path, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def block_peek(self, domname, path, offset, size, buffer, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockPeek(path, offset, size, buffer, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def block_pull(self, domname, device, bandwidth = 0, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockPull(device, bandwidth, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def block_resize(self, domname, device, size, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockResize(device, size, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def block_job_abort(self, domname, device, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockJobAbort(device, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def block_job_set_speed(self, domname, device, bandwidth, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockJobSetSpeed(device, bandwidth, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_block_job_info(self, domname, device, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockJobInfo(device, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_blkio_parameters(self, domname, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blkioParameters(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_block_io_tune(self, domname, device, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockIoTune(device, params, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_blkio_parameters(self, domname, params, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.setBlkioParameters(params, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_block_io_tune(self, domname, device, params, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.setBlockIoTune(device, params, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_memory_parameters(self, domname, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.memoryParameters(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_memory_parameters(self, domname, params, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.setMemoryParameters(params, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def memory_stats(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.memoryStats()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def memory_peek(self, domname, start, size, buffer, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.memoryPeek(start, size, buffer, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def is_active(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.isActive()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def is_persistent(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.isPersistent()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def job_info(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.jobInfo()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def abort_job(self, domname):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.abortJob()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_snapshot_list(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.snapshotListNames(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_snapshot_number(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.snapshotNum(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def get_current_snapshot(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.snapshotCurrent(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def create_snapshot(self, xmldesc, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.snapshotCreateXML(xmldesc, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def set_max_migrate_downtime(self, domname, downtime, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.migrateSetMaxDowntime(downtime, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def migrate_to_uri(self, domname, duri, flags, dname = None, bandwidth = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.migrateToURI(duri, flags, dname, bandwidth)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def attach_device_flag(self, domname, xml, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.attachDeviceFlags(xml, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def dettach_device_flag(self, domname, xml, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.detachDeviceFlags(xml, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def update_device_flag(self, domname, xml, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.updateDeviceFlags(xml, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def managed_save(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.managedSave(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def managedSaveRemove(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.managedSaveRemove(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def blockStats(self, domname, path):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.blockStats(path)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def hasCurrentSnapshot(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.hasCurrentSnapshot(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def hasManagedSaveImage(self, domname, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.hasManagedSaveImage(flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def memoryPeek(self, domname, start, size, buffer, flag = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.memoryPeek(start, size, buffer, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def revertToSnapshot(self, domname, snap, flag):
        try:
            dom_obj = self.get_domain_by_name(domname)
            return dom_obj.revertToSnapshot(snap, flag)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def openConsole(self, domname, device, stream, flags = 0):
        try:
            dom_obj = self.get_domain_by_name(domname)
            st_obj = stream.getStream()
            return dom_obj.openConsole(device, st_obj, flags)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

# DomainState
VIR_DOMAIN_NOSTATE = 0
VIR_DOMAIN_RUNNING = 1
VIR_DOMAIN_BLOCKED = 2
VIR_DOMAIN_PAUSED = 3
VIR_DOMAIN_SHUTDOWN = 4
VIR_DOMAIN_SHUTOFF = 5
VIR_DOMAIN_CRASHED = 6

# virDomainMigrateFlags
VIR_MIGRATE_LIVE = 1
VIR_MIGRATE_PEER2PEER = 2
VIR_MIGRATE_TUNNELLED = 4
VIR_MIGRATE_PERSIST_DEST = 8
VIR_MIGRATE_UNDEFINE_SOURCE = 16
VIR_MIGRATE_PAUSED = 32
VIR_MIGRATE_NON_SHARED_DISK = 64
VIR_MIGRATE_NON_SHARED_INC = 128

# virDomainModificationImpact
VIR_DOMAIN_AFFECT_CURRENT = 0
VIR_DOMAIN_AFFECT_LIVE = 1
VIR_DOMAIN_AFFECT_CONFIG = 2

# virDomainConsoleFlags
VIR_DOMAIN_CONSOLE_FORCE = 1
VIR_DOMAIN_CONSOLE_SAFE  = 2
