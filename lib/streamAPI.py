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
# Summary: class StreamAPI.
# Description: stream operation.
# Maintainer: xhu <xhu@redhat.com>
# Updated: Tue Nov 9, 2010
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

class StreamAPI(object):
    def __init__(self, connection):
        self.conn = connection

    def abort(self, flag = 0):
        try:
            stream_obj = newStream(flag)
            return stream_obj.abort()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def connect(self, flag = 0):
        try:
            stream_obj = newStream(flag)
            return stream_obj.connect()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def finish(self, flag = 0):
        try:
            stream_obj = newStream(flag)
            return stream_obj.finish()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def recv(self, flag = 0, data, nbytes):
        try:
            stream_obj = newStream(flag)
            return stream_obj.recv(data, nbytes)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def send(self, flag = 0, data, nbytes):
        try:
            stream_obj = newStream(flag)
            return stream_obj.send(data, nbytes)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def eventAddCallback(self, flag = 0, cb, opaque):
        try:
            stream_obj = newStream(flag)
            return stream_obj.eventAddCallback(cb, opaque)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def eventRemoveCallback(self, flag = 0):
        try:
            stream_obj = newStream(flag)
            return stream_obj.eventRemoveCallback()
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

    def eventUpdateCallback(self, flag = 0, events)
        try:
            stream_obj = newStream(flag)
            return stream_obj.eventUpdateCallback(events)
        except libvirt.libvirtError, e:
            message = e.get_error_message()
            code = e.get_error_code()
            raise exception.LibvirtAPI(message, code)

