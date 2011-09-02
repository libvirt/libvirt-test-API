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
# Filename: xmlbuilder.py
# Summary: operation for building domain xml
# Description: The module is to provide operation for building domain xml

__DEBUG__ = False

import os, sys
import xml.dom.minidom
import xmlgenerator

class XmlBuilder:
    """Operation for building domain xml"""
    def write_toxml(self, doc):
        print doc.toprettyxml()

    def add_domain(self, params):
        domain = xmlgenerator.domain_xml(params)
        return domain

    def add_disk(self, params, domain):
        disk = xmlgenerator.disk_xml(params)
        disk_node = domain.importNode(disk.childNodes[0], True)
        domain.getElementsByTagName("devices")[0].insertBefore(
        disk_node, domain.getElementsByTagName("console")[0])

    def add_floppy(self, params, domain):
        floppy = xmlgenerator.floppy_xml(params)
        floppy_node = domain.importNode(floppy.childNodes[0], True)
        domain.getElementsByTagName("devices")[0].insertBefore(
        floppy_node, domain.getElementsByTagName("console")[0])

    def add_cdrom(self, params, domain):
        cdrom = xmlgenerator.disk_xml(params, True)
        cdrom_node = domain.importNode(cdrom.childNodes[0], True)
        domain.getElementsByTagName("devices")[0].insertBefore(
        cdrom_node, domain.getElementsByTagName("console")[0])

    def add_interface(self, params, domain):
        interface = xmlgenerator.interface_xml(params)
        interface_node = domain.importNode(interface.childNodes[0], True)
        domain.getElementsByTagName("devices")[0].insertBefore(
        interface_node, domain.getElementsByTagName("console")[0])
        return interface

    def add_hostdev(self, params, domain):
        hostdev = xmlgenerator.hostdev_xml(params)
        hostdev_node = domain.importNode(hostdev.childNodes[0], True)
        domain.getElementsByTagName("devices")[0].insertBefore(
        hostdev_node, domain.getElementsByTagName("console")[0])
        return hostdev

    def build_domain_install(self, params):
        domain = xmlgenerator.domain_xml(params, True)
        self.add_disk(params, domain)
        if params['guesttype'] != 'xenpv':
            if params.has_key('bootcd'):
                self.add_cdrom(params, domain)
        self.add_interface(params, domain)
        if __DEBUG__:
            self.write_toxml(domain)
        return domain.toxml()

    def build_domain_install_win(self, params):
        domain = xmlgenerator.domain_xml(params, True)
        self.add_disk(params, domain)
        self.add_floppy(params, domain)
        if params.has_key('bootcd'):
            self.add_cdrom(params, domain)
        self.add_interface(params, domain)
        if __DEBUG__:
            self.write_toxml(domain)
        return domain.toxml()

    def build_domain(self, domain):
        if __DEBUG__:
            self.write_toxml(domain)
        return domain.toxml()

    def build_disk(self, params):
        if params.get('hdmodel', None) == None:
            params['hdmodel'] = 'ide'

        if params['hdmodel'] == 'ide':
            target_dev = 'hdb'
        elif params['hdmodel'] == 'virtio':
            target_dev = 'vdb'
        else:
            print 'Wrong harddisk model.'

        disk = xmlgenerator.disk_xml(params)
        if params['guesttype'] == 'xenpv':
            disk.getElementsByTagName("target")[0].setAttribute("dev", "xvdb")
        else:
            disk.getElementsByTagName("target")[0].setAttribute("dev",
                                                                target_dev)
        if __DEBUG__:
            self.write_toxml(disk)
        return disk.toxml()

    def build_cdrom(self, params):
        if params.get('hdmodel', None) == None:
            params['hdmodel'] = 'ide'

        if params['hdmodel'] == 'ide':
            target_dev = 'hdc'
        elif params['hdmodel'] == 'scsi':
            target_dev = 'sdc'
        else:
            print 'Wrong cdrom model.'

        cdrom = xmlgenerator.disk_xml(params, True)
        if params['guesttype'] == 'xenpv':
            cdrom.getElementsByTagName("target")[0].setAttribute("dev", "xvdc")
        else:
            cdrom.getElementsByTagName("target")[0].setAttribute("dev",
                                                                target_dev)
        if __DEBUG__:
            self.write_toxml(cdrom)
        return cdrom.toxml()

    def build_floppy(self, params):
        floppy = xmlgenerator.floppy_xml(params)
        if __DEBUG__:
            self.write_toxml(floppy)
        return floppy.toxml()

    def build_interface(self, params):
        interface = xmlgenerator.interface_xml(params)
        if __DEBUG__:
            self.write_toxml(interface)
        return interface.toxml()

    def build_hostdev(self, params):
        hostdev = xmlgenerator.hostdev_xml(params)
        if __DEBUG__:
            self.write_toxml(hostdev)
        return hostdev.toxml()

    def build_pool(self, params):
        pool = xmlgenerator.pool_xml(params)
        if __DEBUG__:
            self.write_toxml(pool)
        return pool.toxml()

    def build_volume(self, params):
        volume = xmlgenerator.volume_xml(params)
        if __DEBUG__:
            self.write_toxml(volume)
        return volume.toxml()

    def build_network(self, params):
        network = xmlgenerator.network_xml(params)
        if __DEBUG__:
            self.write_toxml(network)
        return network.toxml()

    def build_host_interface(self, params):
        interface = xmlgenerator.host_iface_xml(params)
        if __DEBUG__:
            self.write_toxml(interface)
        return interface.toxml()

    def build_domain_snapshot(self, params):
        snapshot = xmlgenerator.snapshot_xml(params)
        if __DEBUG__:
            self.write_toxml(snapshot)
        return snapshot.toxml()

    def build_secret(self, params):
        secret = xmlgenerator.secret_xml(params)
        if __DEBUG__:
            self.write_toxml(secret)
        return secret.toxml()

    def build_nodedev(self, params):
        nodedev = xmlgenerator.nodedev_xml(params)
        if __DEBUG__:
            self.write_toxml(nodedev)
        return nodedev.toxml()

if __name__ == "__main__":

    xmlobj = XmlBuilder()
    params = {}

    #---------------------
    # get disk xml string
    #---------------------
    print '=' * 30, 'disk xml', '=' * 30
    params['guesttype'] = 'kvm'
    params['guestname'] = 'foo'
    params['hdmodel'] = 'virtio'

    diskxml = xmlobj.build_disk(params)

    #---------------------
    # get cdrom xml string
    #---------------------
    print '=' * 30, 'cdrom xml', '=' * 30
    params['guesttype'] = 'kvm'
    params['guestname'] = 'foo'
    params['hdmodel'] = 'ide'
    params['bootcd'] = '/tmp/cdrom.img'

    cdromxml = xmlobj.build_cdrom(params)

    #---------------------
    # get floppy xml string
    #---------------------
    print '=' * 30, 'floppy xml', '=' * 30
    params['floppysource'] = '/tmp/floppy.img'

    floppyxml = xmlobj.build_floppy(params)

    #--------------------------
    # get interface xml string
    #--------------------------
    print '=' * 30, 'interface xml', '=' * 30
    params['ifacetype'] = 'network'
    params['macaddr'] = '11:22:33:44:55:66'
    params['bridge'] = 'xenbr0'
    params['source'] = 'default'
    params['script'] = 'vif-bridge'
    params['ipaddr'] = '192.168.122.1'
    params['port'] = '5558'
    params['nicmodel'] = 'e1000'

    interfacexml = xmlobj.build_interface(params)

    #---------------------
    # get pool xml string
    #---------------------
    print '=' * 30, 'pool xml', '=' * 30
    params['hypertype'] = 'kvm'
    params['pooltype'] = 'iscsi'
    params['poolname'] = 'iscsiauthtest'
    params['sourceformat'] = 'ext3'
    params['sourcename'] = '10.66.70.226'
    params['sourcepath'] = "iqn.1992-08.com.netapp:sn.135053389"
    params['loginid'] = 'foo'
    params['password'] = 'bar'
    params['sourcepath'] = '/dev/sdb1'
    params['targetpath'] = '/home/gren'

    poolxml = xmlobj.build_pool(params)

    #-----------------------
    # get volume xml string
    #-----------------------
    print '=' * 30, 'volume xml', '=' * 30
    params['poolname'] = 'HostVG'
    params['pooltype'] = 'logical'
    params['volname'] = 'foo.img'
    params['volpath'] = '/dev/HostVG/foo.img'
    params['volformat'] = 'lvm2'
    params['capacity'] = '10'
    params['suffix'] = 'M'


    volumexml = xmlobj.build_volume(params)

    #------------------------
    # get network xml string
    #------------------------
    print '=' * 30, 'network xml', '=' * 30
    params['networkname'] = 'local'
    params['netmode'] = 'nat'
    params['bridgename'] = 'virbr1'
    params['bridgeip'] = '192.168.132.1'
    params['bridgenetmask'] = '255.255.255.0'
    params['netstart'] = '192.168.132.2'
    params['netend'] = '192.168.132.254'

    networkxml = xmlobj.build_network(params)

    #-----------------------
    # get domain xml string
    #-----------------------
    print '=' * 30, 'domain xml', '=' * 30
    params['guesttype'] = 'kvm'
    params['guestname'] = 'rhel5u4'
    params['memory'] = '1048576'
    params['vcpu'] = '2'
    params['inputbus'] = 'usb'
    params['sound'] = 'ac97'
    params['bootcd'] = '/iso/rhel5.iso'

    # get hostdev xml string
    params['devmode'] = 'subsystem'
    # The device type can be specified with 'usb' or 'pci'
    params['devtype'] = 'pci'
    params['vendorid'] = '0x1234'
    params['productid'] = '0xbeef'
    params['bus'] = '0x06'
    params['slot'] = '0x02'
    params['function'] = '0x0'

    domain = xmlobj.add_domain(params)
    xmlobj.add_disk(params, domain)
    xmlobj.add_cdrom(params, domain)
    xmlobj.add_interface(params, domain)
    xmlobj.add_hostdev(params, domain)
    guestxml = xmlobj.build_domain(domain)

    #----------------------------------------
    # get domain xml string for installation
    #----------------------------------------
    print '=' * 30, 'install domain xml', '=' * 30
    params['guesttype'] = 'kvm'
    params['guestname'] = 'rhel5u4'
    params['memory'] = '1048576'
    params['vcpu'] = '2'
    params['kickstart'] = 'http://10.66.70.201/libvirt.ks.cfg'
    params['hdmodel'] = 'virtio'
    params['nicmodel'] = 'virtio'
    params['fullimagepath'] = '/tmp/netfs/rhel5u5'
    params['bootcd'] = '/tmp/custom.iso'

    guestinstxml = xmlobj.build_domain_install(params)


    #----------------------------------------
    # get host interface xml string
    #----------------------------------------
    params['ifacetype'] = 'ethernet'
    params['ifacetype'] = 'bond'
    params['ifacetype'] = 'vlan'
    params['ifacetype'] = 'bridge'
    params['bondmode'] = 'active-backup'
    params['ifacename'] = 'eth4.2'
    params['freq'] = '100'
    params['updelay'] = '10'
    params['carrier'] = 'ioctl'
    params['bondname1'] = 'eth0'
    params['bondname2'] = 'eth1'
    params['bridgename1'] = 'eth0'
    params['bridgename2'] = 'eth1'
    params['mode'] = 'onboot'
    params['tag'] = '42'
    params['vlanname'] = 'eth0'
    params['ipaddress'] = '192.168.10.8'
    params['prefix'] = '24'
    params['route'] = '192.168.1.2'
    params['dhcp'] = 'no'
    params['mtu'] = '1492'
    params['stp'] = 'off'
    params['delay'] = '0.01'
    params['family'] = 'ipv6'

    host_xml = xmlobj.build_host_interface(params)

    #----------------------------------------
    # get domain snapshot xml string
    #----------------------------------------
    params['name'] = 'hello'
    params['description'] = 'hello snapshot'
    snapshot_xml = xmlobj.build_domain_snapshot(params)

    #----------------------------------------
    # get domain secret xml string
    #----------------------------------------
    params['ephemeral'] = 'yes'
    params['private'] = 'yes'
    params['volume'] = '/var/lib/libvirt/images/rhel5u5.img'
    params['description'] = 'hello secret'
    secret_xml = xmlobj.build_secret(params)

    #----------------------------------------
    # get domain secret xml string
    #----------------------------------------
    params['name'] = 'scsi_host6'
    params['host'] = '6'
    params['parent'] = 'scsi_host5'
    params['wwnn'] = '2001001b32a9f25b'
    params['wwpn'] = '2101001b32a90001'
    nodedev_xml = xmlobj.build_nodedev(params)

