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
# Summary: class event.
# Description: event operation.
# Maintainer: Guannan Ren <gren@redhat.com>
# Updated: Mon Aug 29, 2011
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

class EventAPI(object):
    def __init__(self):
        pass

    def register_default_impl(self):
        try:
            return libvirt.virEventRegisterDefaultImpl()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def register_impl(self, addHandle,
                            updateHandle,
                            removeHandle,
                            addTimeout,
                            updateTimeout,
                            removeTimeout):
        try:
            return libvirt.virEventRegisterImpl(addHandle,
                                                updateHandle,
                                                removeHandle,
                                                addTimeout,
                                                updateTimeout,
                                                removeTimeout)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def add_handle(self, fd, events, cb, opaque):
        try:
            return libvirt.virEventAddHandle(fd, events, cb, opaque)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def update_handle(self, watch, events):
        try:
            return libvirt.virEventUpdateHandle(watch, events)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def remove_handle(self, watch):
        try:
            return libvirt.virEventRemoveHandle(watch)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def add_timeout(self, timeout, cb, opaque):
        try:
            return libvirt.virEventAddTimeout(timeout, cb, opaque)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def update_timeout(self, timer, timeout):
        try:
            return libvirt.virEventUpdateTimeout(timer, timeout)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def remove_timeout(self, timer):
        try:
            return libvirt.virEventRemoveTimeout(timer)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def run_default_impl(self):
        try:
            return libvirt.virEventRunDefaultImpl()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)
