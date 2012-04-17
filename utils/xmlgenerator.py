#!/usr/bin/env python
#
# Copyright (C) 2010-2012 Red Hat, Inc.
#
# libvirt-test-API is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranties of
# TITLE, NON-INFRINGEMENT, MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Filename: xmlgenerator.py
# Summary: generate domain xml
# Description: The module is a tool to generate domain xml

import os
import sys

sys.path.append("../utils")

import xml.dom.minidom
import utils
import check
import commands

def domain_xml(params, install = False):
    domain = xml.dom.minidom.Document()
    domain_element = domain.createElement('domain')
    domain.appendChild(domain_element)
    if params['guesttype'] == 'xenpv' or params['guesttype'] == 'xenfv':
        domain_element.setAttribute('type', 'xen')
    elif params['guesttype'] == 'kvm' or params['guesttype'] == 'qemu':
        domain_element.setAttribute('type', params['guesttype'])
    else:
        print 'Wrong guest type was set.'
        sys.exit(1)

    # <name>
    name_element = domain.createElement('name')
    name_node = domain.createTextNode(params['guestname'])
    name_element.appendChild(name_node)
    domain_element.appendChild(name_element)

    # <uuid>
    if params.has_key('uuid'):
        uuid_element = domain.createElement('uuid')
        uuid_node = domain.createTextNode(params['uuid'])
        uuid_element.appendChild(uuid_node)
        domain_element.appendChild(uuid_element)

    # <memory>
    memory_element = domain.createElement('memory')
    if params.has_key('memory'):
        memory_node = domain.createTextNode(params['memory'])
    else:
        memory_node = domain.createTextNode('1048576')
    memory_element.appendChild(memory_node)
    domain_element.appendChild(memory_element)

    # <vcpu>
    vcpu_element = domain.createElement('vcpu')
    if params.has_key('vcpu'):
        vcpu_node = domain.createTextNode(params['vcpu'])
    else:
        vcpu_node = domain.createTextNode('1')
    vcpu_element.appendChild(vcpu_node)
    domain_element.appendChild(vcpu_element)

    if not install:
        # <bootloader>
        if params['guesttype'] == 'xenpv':
            bootloader_element = domain.createElement('bootloader')
            bootloader_node = domain.createTextNode('/usr/bin/pygrub')
            bootloader_element.appendChild(bootloader_node)
            domain_element.appendChild(bootloader_element)

    # <os> -- START
    os_element = domain.createElement('os')
    domain_element.appendChild(os_element)

    if not install:
        # <type>
        type_element = domain.createElement('type')
        if params['guesttype'] == 'xenpv':
            type_element.setAttribute('machine', 'xenpv')
            type_node = domain.createTextNode('linux')
        elif params['guesttype'] == 'xenfv':
            type_element.setAttribute('machine', 'xenfv')
            type_node = domain.createTextNode('hvm')
        elif params['guesttype'] == 'kvm' or params['guesttype'] == 'qemu':
            type_element.setAttribute('machine', 'pc')
            type_node = domain.createTextNode('hvm')
        else:
            print 'Wrong guest type was set.'
            sys.exit(1)
        type_element.appendChild(type_node)
        os_element.appendChild(type_element)

        # <loader>
        if params['guesttype'] == 'xenfv':
            loader_element = domain.createElement('loader')
            loader_node = domain.createTextNode('/usr/lib/xen/boot/hvmloader')
            loader_element.appendChild(loader_node)
            os_element.appendChild(loader_element)

        # <boot>
        if params['guesttype'] != 'xenpv':
            boot_element = domain.createElement('boot')
            boot_element.setAttribute('dev', 'hd')
            os_element.appendChild(boot_element)

    elif install:
        if params['guesttype'] == 'xenpv' \
            or (params['guesttype'] == 'kvm' and not params.has_key('bootcd')) \
            or (params['guesttype'] == 'qemu' and not params.has_key('bootcd')):
            # <type>
            type_element = domain.createElement('type')
            if params['guesttype'] == 'xenpv':
                type_node = domain.createTextNode('linux')
            if params['guesttype'] == 'kvm' or params['guesttype'] == 'qemu':
                type_node = domain.createTextNode('hvm')
            type_element.appendChild(type_node)
            os_element.appendChild(type_element)
            # <kernel>
            kernel_element = domain.createElement('kernel')
            kernel_node = domain.createTextNode('/var/lib/libvirt/boot/vmlinuz')
            kernel_element.appendChild(kernel_node)
            os_element.appendChild(kernel_element)
            # <initrd>
            initrd_element = domain.createElement('initrd')
            initrd_node = domain.createTextNode(
                          '/var/lib/libvirt/boot/initrd.img')
            initrd_element.appendChild(initrd_node)
            os_element.appendChild(initrd_element)
            # <cmdline>
            cmdline_element = domain.createElement('cmdline')
            cmdline_node = domain.createTextNode('ks=' + params['kickstart'])
            cmdline_element.appendChild(cmdline_node)
            os_element.appendChild(cmdline_element)
            if params['guesttype'] != 'xenpv':
                # <boot>
                boot_element = domain.createElement('boot')
                boot_element.setAttribute('dev', 'hd')
                os_element.appendChild(boot_element)

        elif params['guesttype'] == 'xenfv' \
            or (params['guesttype'] == 'kvm' and params.has_key('bootcd')) \
            or (params['guesttype'] == 'qemu' and params.has_key('bootcd')):
            # <type>
            type_element = domain.createElement('type')
            type_node = domain.createTextNode('hvm')
            type_element.appendChild(type_node)
            os_element.appendChild(type_element)
            if params['guesttype'] == 'xenfv':
                # <loader>
                loader_element = domain.createElement('loader')
                loader_node = domain.createTextNode(
                              '/usr/lib/xen/boot/hvmloader')
                loader_element.appendChild(loader_node)
                os_element.appendChild(loader_element)
            # <boot>
            boot_element = domain.createElement('boot')
            boot_element.setAttribute('dev', 'cdrom')
            os_element.appendChild(boot_element)
    else:
        print 'Please specific install flag.'
    # </os> -- END

    # <features>
    if params['guesttype'] != 'xenpv':
        features_element = domain.createElement('features')
        domain_element.appendChild(features_element)
        acpi_element = domain.createElement('acpi')
        features_element.appendChild(acpi_element)
        apic_element = domain.createElement('apic')
        features_element.appendChild(apic_element)
        pae_element = domain.createElement('pae')
        features_element.appendChild(pae_element)

    # <clock>
    clock_element = domain.createElement('clock')
    clock_element.setAttribute('offset', 'utc')
    domain_element.appendChild(clock_element)

    # <on_poweroff>
    poweroff_element = domain.createElement('on_poweroff')
    poweroff_node = domain.createTextNode('destroy')
    poweroff_element.appendChild(poweroff_node)
    domain_element.appendChild(poweroff_element)

    # <on_reboot>
    reboot_element = domain.createElement('on_reboot')
    reboot_node = domain.createTextNode('restart')
    reboot_element.appendChild(reboot_node)
    domain_element.appendChild(reboot_element)

    # <on_crash>
    crash_element = domain.createElement('on_crash')
    crash_node = domain.createTextNode('restart')
    crash_element.appendChild(crash_node)
    domain_element.appendChild(crash_element)

    # <devices> -- START
    devices_element = domain.createElement('devices')
#    if params['guesttype'] == 'xenfv':
#        emulator_element = domain.createElement('emulator')
#        host_arch = utils.get_host_arch()
#        if host_arch == 'i386' or host_arch == 'ia64':
#            emulator_node = domain.createTextNode('/usr/lib/xen/bin/qemu-dm')
#        elif host_arch == 'x86_64':
#            emulator_node = domain.createTextNode('/usr/lib64/xen/bin/qemu-dm')
#        else:
#            print 'Wrong arch is specified.'
#            sys.exit(1)
#        emulator_element.appendChild(emulator_node)
#        devices_element.appendChild(emulator_element)
#    if params['guesttype'] == 'kvm' or params['guesttype'] == 'qemu':
#        emulator_element = domain.createElement('emulator')
#        emulator_node = domain.createTextNode('/usr/libexec/qemu-kvm')
#        emulator_element.appendChild(emulator_node)
#        devices_element.appendChild(emulator_element)

    # <console>
    console_element = domain.createElement('console')
    devices_element.appendChild(console_element)

    # <input>
    input_element = domain.createElement('input')
    input_element.setAttribute('type', 'mouse')
    if params['guesttype'] == 'xenpv':
        input_element.setAttribute('bus', 'xen')
    else:
        if params.has_key('inputbus'):
            input_element.setAttribute('bus', params['inputbus'])
        else:
            input_element.setAttribute('bus', 'ps2')
    devices_element.appendChild(input_element)

    # <graphics>
    graphics_element = domain.createElement('graphics')
    graphics_element.setAttribute('type', 'vnc')
    graphics_element.setAttribute('port', '-1')
    graphics_element.setAttribute('keymap', 'en-us')
    devices_element.appendChild(graphics_element)
    domain_element.appendChild(devices_element)

    # <sound>
    # Sound device model: es1370, sb16, ac97
    if params.has_key('sound'):
        sound_element = domain.createElement('sound')
        sound_element.setAttribute('model', params['sound'])
        devices_element.appendChild(sound_element)

    # </devices> -- END
    # </domain> -- END

    return domain

def disk_xml(params, cdrom = False):
    disk = xml.dom.minidom.Document()
    # <disk> -- START
    disk_element = disk.createElement('disk')
    disk_element.setAttribute('type', 'file')
    disk.appendChild(disk_element)
    if not cdrom:
        disk_element.setAttribute('device', 'disk')
    elif cdrom:
        disk_element.setAttribute('device', 'cdrom')
    else:
        print 'Wrong device of disk.'
        sys.exit(1)

    # <driver>
    if not cdrom:
        if params['guesttype'] == 'kvm' or params['guesttype'] == 'qemu':
            driver_element = disk.createElement('driver')
            driver_element.setAttribute('name', 'qemu')
            if params.get('imagetype', None) == None:
                params['imagetype'] = 'raw'
            driver_element.setAttribute('type', params['imagetype'])
            if params.get('cache', None) == None:
                params['cache'] = 'none'
            driver_element.setAttribute('cache', params['cache'])
            disk_element.appendChild(driver_element)
        elif params['guesttype'] == 'xenpv' or params['guesttype'] == 'xenfv':
            driver_element = disk.createElement('driver')
            if params['guesttype'] == 'xenpv':
                driver_element.setAttribute('name', 'tap')
                driver_element.setAttribute('type', 'aio')
            if params['guesttype'] == 'xenfv':
                driver_element.setAttribute('name', 'file')
            disk_element.appendChild(driver_element)
        else:
            print 'Unknown guest type.'
            sys.exit(1)
    elif cdrom:
        if params['guesttype'] == 'xenpv' or params['guesttype'] == 'xenfv':
            driver_element = disk.createElement('driver')
            driver_element.setAttribute('name', 'file')
            disk_element.appendChild(driver_element)
    else:
        print 'Wrong device of disk.'
        sys.exit(1)

    ### Get image path ###
    hypertype = utils.get_hypervisor()
    if not params.has_key('fullimagepath'):
        if hypertype == 'kvm':
            params['imagepath'] = '/var/lib/libvirt/images'
            params['fullimagepath'] = params['imagepath'] + '/' + \
                                      params['guestname']
        elif hypertype == 'xen':
            params['imagepath'] = '/var/lib/xen/images'
            params['fullimagepath'] = params['imagepath'] + '/' + \
                                      params['guestname']
        else:
            print 'DO NOT supported hypervisor.'
            sys.exit(1)

    # <source>
    source_element = disk.createElement('source')
    disk_element.appendChild(source_element)
    if not cdrom:
        if not params.has_key('imagename'):
            source_element.setAttribute('file', params['fullimagepath'])
        else:
            source_element.setAttribute('file', params['imagepath'] + '/' + \
                                         params['imagename'] + '.img')
    elif cdrom:
        source_element.setAttribute('file', params['bootcd'])
    else:
        print 'Wrong device of disk.'
        sys.exit(1)

    # <target>
    target_element = disk.createElement('target')
    disk_element.appendChild(target_element)

    if params.get('hdmodel', None) == None:
        params['hdmodel'] = 'ide'

    if params['hdmodel'] == 'ide':
        target_dev = 'hda'
    elif params['hdmodel'] == 'virtio':
        target_dev = 'vda'
    else:
        print 'Wrong disk target device is specified.'

    if not cdrom:
        if params['guesttype'] == 'xenpv':
            target_element.setAttribute('dev', 'xvda')
            target_element.setAttribute('bus', 'xen')
        else:
            target_element.setAttribute('dev', target_dev)
            target_element.setAttribute('bus', params['hdmodel'])
    elif cdrom:
        target_element.setAttribute('dev', 'hdc')
        target_element.setAttribute('bus', 'ide')
    else:
        print 'Wrong device of disk.'
        sys.exit(1)

    if cdrom:
        readonly_element = disk.createElement('readonly')
        disk_element.appendChild(readonly_element)
    # </disk> -- END

    return disk

def floppy_xml(params):
    # Disk element
    floppy = xml.dom.minidom.Document()
    floppy_element = floppy.createElement('disk')
    floppy_element.setAttribute('type', 'file')
    floppy_element.setAttribute('device', 'floppy')
    floppy.appendChild(floppy_element)

    # Source element
    source_element = floppy.createElement('source')
    source_element.setAttribute('file', params['floppysource'])
    floppy_element.appendChild(source_element)

    # Target element
    target_element = floppy.createElement('target')
    if params.has_key('floppytarget'):
        target_element.setAttribute('dev', params['floppytarget'])
    else:
        target_element.setAttribute('dev', 'fda')

    target_element.setAttribute('bus', 'fdc')
    floppy_element.appendChild(target_element)

    # Readonly
    readonly = floppy.createElement('readonly')
    floppy_element.appendChild(readonly)

    return floppy


def interface_xml(params):
    interface = xml.dom.minidom.Document()
    # <interface> -- START
    interface_element = interface.createElement('interface')
    # Network interfaces type: network bridge user ethernet mcast server client
    if params.get('ifacetype', None) == None:
        params['ifacetype'] = 'network'
    if params.get('source', None) == None:
        params['source'] = 'default'
    interface_element.setAttribute('type', params['ifacetype'])
    interface.appendChild(interface_element)

    # <source>
    if params['ifacetype'] != 'user' and params['ifacetype'] != 'ethernet':
        source_element = interface.createElement('source')
        interface_element.appendChild(source_element)
    if params['ifacetype'] == 'network':
        if params.has_key('source'):
            source_element.setAttribute('network', params['source'])
    if params['ifacetype'] == 'bridge':
        if params.has_key('source'):
            source_element.setAttribute('bridge', params['source'])
    if params['ifacetype'] == 'mcast' or params['ifacetype'] == 'server' or \
       params['ifacetype'] == 'client':
        source_element.setAttribute('address', params['ipaddr'])
        source_element.setAttribute('port', params['port'])

    # <model>
    # Network device model: ne2k_isa i82551 i82557b i82559er ne2k_pci
    # pcnet rtl8139 e1000 virtio
    host_release = utils.get_host_kernel_version()
    if 'el6' in host_release:
        if params.has_key('nicmodel'):
            model_element = interface.createElement('model')
            model_element.setAttribute('type', params['nicmodel'])
            interface_element.appendChild(model_element)

    # <mac>
    MacAddr = utils.get_rand_mac()
    if params.has_key('macaddr'):
        mac_element = interface.createElement('mac')
        mac_element.setAttribute('address', params['macaddr'])
        interface_element.appendChild(mac_element)
    elif params.get('macaddr', None) == None:
        mac_element = interface.createElement('mac')
        mac_element.setAttribute('address', MacAddr)
        interface_element.appendChild(mac_element)

    # <script>
    if params['ifacetype'] == 'bridge' or params['ifacetype'] == 'ethernet':
        script_element = interface.createElement('script')
        script_element.setAttribute('path', 'vif-bridge')
        interface_element.appendChild(script_element)
    # <interface> -- END

    return interface


def pool_xml(params):
    pool = xml.dom.minidom.Document()
    # <pool> -- START
    pool_element = pool.createElement('pool')
    pool_element.setAttribute('type', params['pooltype'])
    pool.appendChild(pool_element)

    # <name>
    name_element = pool.createElement('name')
    name_node = pool.createTextNode(params['poolname'])
    name_element.appendChild(name_node)
    pool_element.appendChild(name_element)

    # <source> -- START
    if params['pooltype'] != 'dir':
        source_element = pool.createElement('source')
        pool_element.appendChild(source_element)

        # <host>
        if params['pooltype'] == 'netfs' or params['pooltype'] == 'iscsi':
            host_element = pool.createElement('host')
            host_element.setAttribute('name', params['sourcename'])
            source_element.appendChild(host_element)

        # <name>
        if params['pooltype'] == 'logical':
            sourcename_element = pool.createElement('name')
            sourcename_node = pool.createTextNode(params['sourcename'])
            sourcename_element.appendChild(sourcename_node)
            source_element.appendChild(sourcename_element)

        # <dir>
        if params['pooltype'] == 'netfs':
            dir_element = pool.createElement('dir')
            dir_element.setAttribute('path', params['sourcepath'])
            source_element.appendChild(dir_element)

        # <format>
        if params['pooltype'] == 'netfs' or params['pooltype'] == 'disk' \
        or params['pooltype'] == 'fs' \
        or params['pooltype'] == 'logical':
            if params.has_key('sourceformat'):
                format_element = pool.createElement('format')
                format_element.setAttribute('type', params['sourceformat'])
                source_element.appendChild(format_element)
            else:
                if params['pooltype'] == 'netfs':
                    format_element = pool.createElement('format')
                    format_element.setAttribute('type', 'nfs')
                    source_element.appendChild(format_element)
                if params['pooltype'] == 'disk':
                    format_element = pool.createElement('format')
                    format_element.setAttribute('type', 'dos')
                    source_element.appendChild(format_element)
                if params['pooltype'] == 'fs':
                    format_element = pool.createElement('format')
                    format_element.setAttribute('type', 'ext3')
                    source_element.appendChild(format_element)
                if params['pooltype'] == 'logical':
                    format_element = pool.createElement('format')
                    format_element.setAttribute('type', 'lvm2')
                    source_element.appendChild(format_element)

        # <device>
        if params['pooltype'] == 'disk' or params['pooltype'] == 'fs' \
            or params['pooltype'] == 'iscsi' \
            or params['pooltype'] == 'logical':
            device_element = pool.createElement('device')
            device_element.setAttribute('path', params['sourcepath'])
            source_element.appendChild(device_element)

        # <auth>
        if params['pooltype'] == 'iscsi' and params.has_key('loginid') \
            and params.has_key('password'):
            auth_element = pool.createElement('auth')
            auth_element.setAttribute('type', 'chap')
            auth_element.setAttribute('login', params['loginid'])
            auth_element.setAttribute('passwd', params['password'])
            source_element.appendChild(auth_element)

        #<adapter>
        if params['pooltype'] == 'scsi':
            adapter_element = pool.createElement('adapter')
            adapter_element.setAttribute('name', params['sourcename'])
            source_element.appendChild(adapter_element)
    else:
        source_element = pool.createElement('source')
        pool_element.appendChild(source_element)
    # <source> -- END

    # <target> -- START
    target_element = pool.createElement('target')
    pool_element.appendChild(target_element)

    ### Get image path ###
    if not params.has_key('targetpath'):
        if params['pooltype'] == 'netfs' or params['pooltype'] == 'dir':
            if utils.get_hypervisor() == 'kvm':
                params['targetpath'] = '/var/lib/libvirt/images'
            elif utils.get_hypervisor() == 'xen':
                params['targetpath'] = '/var/lib/xen/images'
            else:
                print 'NOT supported hypervisor.'
                sys.exit(1)
        if params['pooltype'] == 'iscsi':
            params['targetpath'] = '/dev/disk/by-path'
        if params['pooltype'] == 'logical':
            params['targetpath'] = '/dev/%s' % params['poolname']
        if params['pooltype'] == 'disk':
            params['targetpath'] = '/dev'
        if params['pooltype'] == 'fs':
            params['targetpath'] = '/mnt'
        if params['pooltype'] == 'scsi':
            params['targetpath'] = '/dev/disk/by-path'
        if params['pooltype'] == 'mpath':
            params['targetpath'] = '/dev/mapper'

    # <path>
    path_element = pool.createElement('path')
    path_node = pool.createTextNode(params['targetpath'])

    path_element.appendChild(path_node)
    target_element.appendChild(path_element)
    # <target> -- END
    # <pool> -- END

    return pool


def volume_xml(params):
    volume = xml.dom.minidom.Document()
    # <volume> -- START
    volume_element = volume.createElement('volume')
    volume.appendChild(volume_element)

    # <name>
    name_element = volume.createElement('name')
    name_node = volume.createTextNode(params['volname'])
    name_element.appendChild(name_node)
    volume_element.appendChild(name_element)

    # <capacity>
    capacity_element = volume.createElement('capacity')
    capacity_node = volume.createTextNode(params['capacity'])
    if params.has_key('suffix'):
        capacity_element.setAttribute('unit', params['suffix'])
    capacity_element.appendChild(capacity_node)
    volume_element.appendChild(capacity_element)

    # <allocation>
    allocation_element = volume.createElement('allocation')
    if params['pooltype'] == 'dir' or params['pooltype'] == 'netfs':
        allocation_node = volume.createTextNode('0')
    else:
        if params.has_key('suffix'):
            allocation_element.setAttribute('unit', params['suffix'])
        if params.get('allocation', None) == None:
            params['allocation'] = params['capacity']
        allocation_node = volume.createTextNode(params['allocation'])
    allocation_element.appendChild(allocation_node)
    volume_element.appendChild(allocation_element)

    # <target> -- START
    target_element = volume.createElement('target')
    volume_element.appendChild(target_element)

    # <path>
    if params['pooltype'] != 'disk':
        path_element = volume.createElement('path')
        path_node = volume.createTextNode(params['volpath'])
        path_element.appendChild(path_node)
        target_element.appendChild(path_element)

    # <format>
    if params['pooltype'] != 'logical':
        format_element = volume.createElement('format')
        format_element.setAttribute('type', params['volformat'])
        target_element.appendChild(format_element)
    # <target> -- END
    # <volume> -- END

    return volume


def network_xml(params):
    network = xml.dom.minidom.Document()
    # <network> -- START
    network_element = network.createElement('network')
    network.appendChild(network_element)

    # <name>
    name_element = network.createElement('name')
    name_node = network.createTextNode(params['networkname'])
    name_element.appendChild(name_node)
    network_element.appendChild(name_element)

    # <forward>
    if params.get('netmode', None) != None:
        if params['netmode'] == 'nat' or params['netmode'] == 'route':
            forward_element = network.createElement('forward')
            forward_element.setAttribute('mode', params['netmode'])
            network_element.appendChild(forward_element)

    # <bridge>
    bridge_element = network.createElement('bridge')
    bridge_element.setAttribute('name', params['bridgename'])
    bridge_element.setAttribute('stp', 'on')
    bridge_element.setAttribute('forwardDelay', '0')
    network_element.appendChild(bridge_element)

    # <ip>
    ip_element = network.createElement('ip')
    ip_element.setAttribute('address', params['bridgeip'])
    ip_element.setAttribute('netmask', params['bridgenetmask'])
    # <dhcp>
    dhcp_element = network.createElement('dhcp')
    ip_element.appendChild(dhcp_element)
    # <range>
    range_element = network.createElement('range')
    range_element.setAttribute('start', params['netstart'])
    range_element.setAttribute('end', params['netend'])
    dhcp_element.appendChild(range_element)
    # <dhcp> -- END
    network_element.appendChild(ip_element)
    # <ip> -- END
    # <network> -- END

    return network

def hostdev_xml(params):
    hostdev = xml.dom.minidom.Document()
    # <hostdev> -- START
    hostdev_element = hostdev.createElement('hostdev')
    hostdev_element.setAttribute('mode', params['devmode'])
    hostdev_element.setAttribute('type', params['devtype'])
    hostdev.appendChild(hostdev_element)

    # <source>
    source_element = hostdev.createElement('source')
    hostdev_element.appendChild(source_element)

    if params['devtype'] == 'usb':
        # <vendor>
        vendor_element = hostdev.createElement('vendor')
        vendor_element.setAttribute('id', params['vendorid'])
        source_element.appendChild(vendor_element)

        # <product>
        product_element = hostdev.createElement('product')
        product_element.setAttribute('id', params['productid'])
        source_element.appendChild(product_element)

    if params['devtype'] == 'pci':
        # <address>
        address_element = hostdev.createElement('address')
        address_element.setAttribute('bus', params['bus'])
        address_element.setAttribute('slot', params['slot'])
        address_element.setAttribute('function', params['function'])
        source_element.appendChild(address_element)
    # <source> -- END
    # <hostdev> -- END

    return hostdev

def host_iface_xml(params):
    interface = xml.dom.minidom.Document()
    # <interface>
    interface_element = interface.createElement('interface')
    # Host network interfaces type: ethernet
    if params.get('ifacetype', None) == None:
        interface_element.setAttribute('type', 'ethernet')
    else:
        interface_element.setAttribute('type', params['ifacetype'])
    if params.get('ifacename', None) == None:
        interface_element.setAttribute('name', 'ethX')
    else:
        interface_element.setAttribute('name', params['ifacename'])
    interface.appendChild(interface_element)

    # <mode>
    mode_element = interface.createElement('start')
    interface_element.appendChild(mode_element)
    if not params.has_key('mode'):
        mode_element.setAttribute('mode', 'none')
    else:
        mode_element.setAttribute('mode', params['mode'])

    # <protocol>
    protocol_element = interface.createElement('protocol')
    interface_element.appendChild(protocol_element)
    if params.has_key('family'):
        protocol_element.setAttribute('family', params['family'])
    else:
        protocol_element.setAttribute('family', 'ipv4')

    if params.has_key('ipaddress'):
        ip_element = interface.createElement('ip')
        protocol_element.appendChild(ip_element)

        ip_element.setAttribute('address', params['ipaddress'])
        ip_element.setAttribute('prefix', params['prefix'])

    if params.has_key('route'):
        route_element = interface.createElement('route')
        if params.has_key('gateway'):
            route_element.setAttribute('gateway', params['gateway'])
        protocol_element.appendChild(route_element)

    if params.has_key('dhcp'):
        dhcp_element = interface.createElement('dhcp')
        if params['ifacetype'] != 'bridge' \
        and params.get('family', None) != 'ipv6':
            dhcp_element.setAttribute('peerdns', 'no')
        protocol_element.appendChild(dhcp_element)

        if params.get('family', None) != 'ipv6' \
                and params.has_key('mtu'):
            mtu_element = interface.createElement('mtu')
            mtu_element.setAttribute('size', params['mtu'])
            interface_element.appendChild(mtu_element)

    if params['ifacetype'] == 'bond':
        bond_element = interface.createElement('bond')
        bond_element.setAttribute('mode', params['bondmode'])
        interface_element.appendChild(bond_element)

        miimon_element = interface.createElement('miimon')
        miimon_element.setAttribute('freq', params['freq'])
        miimon_element.setAttribute('updelay', params['updelay'])
        miimon_element.setAttribute('carrier', params['carrier'])
        bond_element.appendChild(miimon_element)

    if params['ifacetype'] == 'bridge':
        bridge_element = interface.createElement('bridge')
        bridge_element.setAttribute('stp', params['stp'])
        bridge_element.setAttribute('delay', params['delay'])
        interface_element.appendChild(bridge_element)

    if params['ifacetype'] == 'bond' or params['ifacetype'] == 'bridge':
        common1_iface_element = interface.createElement('interface')
        # Host network interfaces type: ethernet
        if params.get('%sifacetype' %params['ifacetype'], None) == None:
            common1_iface_element.setAttribute('type', 'ethernet')
        else:
            common1_iface_element.setAttribute('type', params['ifacetype'])
        common1_iface_element.setAttribute('name',
        params['%sname1' %params['ifacetype']])

        if params['ifacetype'] == 'bond':
            bond_element.appendChild(common1_iface_element)
        if params['ifacetype'] == 'bridge':
            bridge_element.appendChild(common1_iface_element)

        common2_iface_element = interface.createElement('interface')
        # Host network interfaces type: ethernet
        if params.get('%sifacetype' %params['ifacetype'], None) == None:
            common2_iface_element.setAttribute('type', 'ethernet')
        else:
            common2_iface_element.setAttribute('type', params['ifacetype'])
        common2_iface_element.setAttribute('name',
        params['%sname2' %params['ifacetype']])

        if params['ifacetype'] == 'bond':
            bond_element.appendChild(common2_iface_element)
        if params['ifacetype'] == 'bridge':
            bridge_element.appendChild(common2_iface_element)

    if params['ifacetype'] == 'vlan':
        vlan_element = interface.createElement('vlan')
        vlan_element.setAttribute('tag', params['tag'])
        interface_element.appendChild(vlan_element)

        vlan_iface_element = interface.createElement('interface')
        # Host network interfaces type: ethernet
        vlan_iface_element.setAttribute('name', params['vlanname'])
        vlan_element.appendChild(vlan_iface_element)

    return interface

def snapshot_xml(params):
    snapshot = xml.dom.minidom.Document()
    # <domainsnapshot>
    dom_snapshot_element = snapshot.createElement('domainsnapshot')
    # <name>
    name_element = snapshot.createElement('name')
    name_node = snapshot.createTextNode(params['snapshotname'])
    name_element.appendChild(name_node)
    dom_snapshot_element.appendChild(name_element)
    # <description> is optional
    if params.has_key('description'):
        desc_element = snapshot.createElement('description')
        desc_node = snapshot.createTextNode(params['description'])
        desc_element.appendChild(desc_node)
        dom_snapshot_element.appendChild(desc_element)

    snapshot.appendChild(dom_snapshot_element)
    return snapshot

def secret_xml(params):
    secret = xml.dom.minidom.Document()
    # <secret>
    secret_element = secret.createElement('secret')
    if params.get('ephemeral', None) == None:
        secret_element.setAttribute('ephemeral', 'no')
    else:
        secret_element.setAttribute('ephemeral', params['ephemeral'])
    if params.get('private', None) == None:
        secret_element.setAttribute('private', 'no')
    else:
        secret_element.setAttribute('private', params['private'])
    # <description> is optional
    if params.has_key('description'):
        desc_element = secret.createElement('description')
        desc_node = secret.createTextNode(params['description'])
        desc_element.appendChild(desc_node)
        secret_element.appendChild(desc_element)
    # <usage>
    usage_element = secret.createElement('usage')
    usage_element.setAttribute('type', 'volume')
    secret_element.appendChild(usage_element)
    # <volume>
    volume_element = secret.createElement('volume')
    volume_node = secret.createTextNode(params['volume'])
    volume_element.appendChild(volume_node)
    usage_element.appendChild(volume_element)

    secret.appendChild(secret_element)
    return secret

def nodedev_xml(params):
    nodedev = xml.dom.minidom.Document()
    # <device>
    device_element = nodedev.createElement('device')
    nodedev.appendChild(device_element)
    # <name>
    # <parent>
    parent_element = nodedev.createElement('parent')
    parent_node = nodedev.createTextNode(params['parent'])
    parent_element.appendChild(parent_node)
    device_element.appendChild(parent_element)
    # <capability>
    capability_element = nodedev.createElement('capability')
    capability_element.setAttribute('type', 'scsi_host')
    device_element.appendChild(capability_element)
    # <host>
    # <capability>
    capability1_element = nodedev.createElement('capability')
    capability1_element.setAttribute('type', 'fc_host')
    capability_element.appendChild(capability1_element)
    # <wwnn>
    wwnn_element = nodedev.createElement('wwnn')
    wwnn_node = nodedev.createTextNode(params['wwnn'])
    wwnn_element.appendChild(wwnn_node)
    capability1_element.appendChild(wwnn_element)
    # <wwpn>
    wwpn_element = nodedev.createElement('wwpn')
    wwpn_node = nodedev.createTextNode(params['wwpn'])
    wwpn_element.appendChild(wwpn_node)
    capability1_element.appendChild(wwpn_element)

    return nodedev
