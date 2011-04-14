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
# Filename: env_parser.py 
# Summary: parse the env configuration file 
# Description: The module is a tool to parse the env configuration file 
# Maintainer: gren@redhat.com
# Version: 0.1.0

import ConfigParser
import os
import sys

dir = os.path.dirname(sys.modules[__name__].__file__)
absdir = os.path.abspath(dir)
sys.path.append(os.path.split(absdir)[0])

import exception

class Envparser(object):
    def __init__(self, configfile):
        self.cfg = ConfigParser.ConfigParser()
        if os.path.isfile(configfile):
            self.cfg.read(configfile)
        else:
            raise exception.FileDoesNotExist(
            "env.conf is not a regular file or nonexist")     

    def has_section(self, section):
        if self.cfg.has_section(section):
            return True
        else:
            return False

    def has_option(self, section, option):
        if self.has_section(section):
            if self.cfg.has_option(section, option):
                return True
            else:
                return False
        else:
            raise exception.SectionDoesNotExist(
            "In env.conf, the section %s is nonexist" % section) 

    def sections_list(self):
        return self.cfg.sections()

    def options_list(self, section):
        if self.has_section:
            return self.cfg.options(section)        
        else:
            raise exception.SectionDoesNotExist(
            "In env.conf, the section %s is nonexist" % section) 
         
    def get_value(self, section, option):
        if self.has_section:
            if self.has_option:
                return self.cfg.get(section, option)
            else:
                raise exception.OptionDoesNotExist(
                "In env.conf, the option %s is nonexist" % option)
        else:
            raise exception.SectionDoesNotExist(
            "In env.conf, the section %s is nonexist" % section)

    def get_items(self, section):
        if self.has_section:
            return self.cfg.items(section)
        else:
            raise exception.SectionDoesNotExist(
            "In env.conf, the section %s is nonexist" % section)

    def add_section(self, section):
        if self.has_section:
            raise exception.SectionExist(
            "Section %s exists already" % section)
        else:
            self.cfg.add_section(section) 
            return True
 
    def remove_option(self, section, option):
        if self.has_section:
            if self.has_option:
                self.cfg.remove_option(section, option)
                return True
            else:
                raise exception.OptionDoesNotExist(
                "In env.conf, the option %s is nonexist" % option)
        else:
            raise exception.SectionDoesNotExist(
            "In env.conf, the section %s is nonexist" % section)
      
    def remove_section(self, section):
        if self.has_section:
            self.cfg.remove_section(section)
            return True
        else:
            raise exception.SectionDoesNotExist(
            "In env.conf, the section %s is nonexist" % section)
  
    def set_value(self, section, option, value):
        if self.has_section:
            if self.has_option:
                self.cfg.set(section, option, value)
                return True
            else:
                raise exception.OptionDoesNotExist(
                "In env.conf, the option %s is nonexist" % option)
        raise exception.SectionDoesNotExist(
        "In env.conf, the section %s is nonexist" % section)

