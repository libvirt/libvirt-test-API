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
# Filename: generator.py 
# Summary: parse case configuration file  
# Description: the module is for configuration file parsing to 
#              generate a case list   
# Maintainer: gren@redhat.com
# Updated: Oct 19 2009
# Version: 0.1.0

import re
import os
import sys
import copy

class CaseFileParser(object):
    """ Parser the case configuration file to generate a data list.
    """
    def __init__(self, casefile=None, debug=False):
        """ Initialize the list and optionally parse case file. """
        self.list = [[]]
        self.debug = debug
        self.casefile = casefile
        if casefile:
            self.parse_file(casefile)

    def set_debug(self, debug=False):
        """ Enable or disable debugging support. """
        self.debug = debug

    def parse_file(self, casefile):        
        """ Open casefile for parsering. """ 
        if not os.path.exists(casefile):
            raise Exception, "File %s not found" % casefile
        self.casefile = casefile
        file = open(casefile, "r")
        self.list = self.parse(file, self.list)
        file.close()
        return self.list

    def get_list(self):
        """ Return the list of dictionaries.
        """
        return self.list

    def get_next_line(self, file):
        """ Get the next non-empty, non-comment line in file.
            If no line is available, return None.
        """
        while True:
            line = file.readline()
            if line == "": return None
            stripped_line = line.strip()
            if len(stripped_line) > 0 \
                    and not stripped_line.startswith('#') \
                    and not stripped_line.startswith('//'):
                return line

    def get_next_line_indent(self, file):
        """ Return the indent level of the next non-empty, 
            non-comment line in file.If no line is available, return -1.
        """
        pos = file.tell()
        line = self.get_next_line(file)
        if not line:
            file.seek(pos)
            return -1
        line = line.expandtabs()
        indent = 0
        while line[indent] == ' ':
            indent += 1
        file.seek(pos)
        return indent

    def add_option_value(self, caselist, casename, option, value):
        """ Add option to the data list. """ 
        for dictionary in caselist:
            testkey = dictionary.keys()[0]
            if casename == testkey:
                if not dictionary[testkey].has_key(option):
                    dictionary[testkey][option] = value      
            else:
                continue    

    def debug_print(self, str1, str2=""):
        """Nicely print two strings and an arrow.  For internal use."""
        if str2:
            str = "%-50s ---> %s" % (str1, str2)
        else:
            str = str1
        print str
            
    def option_parse(self, file, list, casename):
        """ For options of a case parsing. """
        new_list = []

        indent = self.get_next_line_indent(file)
        if indent != 4:
            print "wrong format"
            sys.exit(1)
        else:
            optionname = self.get_next_line(file)
            if optionname:
                tripped_optionname = optionname.strip()

            if self.debug:
                self.debug_print("the option name is %s" % tripped_optionname)

            while True:
                temp_list = []

                indent = self.get_next_line_indent(file)
                if indent == -1:
                    break
               
                for caselist in list:
                    new_dict = copy.deepcopy(caselist)
                    temp_list.append(new_dict)

                if indent != 8 and indent == 4:
                    new_list = self.option_parse(file, new_list, casename)
                    return new_list
                elif indent == 0:
                    new_list = self.parse(file, new_list)
                    return new_list
                else:
                    valuestring = self.get_next_line(file)

                    tripped_valuelist = valuestring.strip().split()
                    tripped_valuename = tripped_valuelist[0]
                     
                    if self.debug:
                        self.debug_print(
                            "the option_value we are parsing is %s" %
                             tripped_valuename)
                        self.debug_print("the temp_list is %s" % temp_list)

                    filterter_list = []

                    for caselist in temp_list:
                        if self.debug:
                            self.debug_print(
                                "before parsing, the caselist is %s" % 
                                caselist)

                        if len(tripped_valuelist) > 1:
                            if tripped_valuelist[1] == "only" and \
                                len(tripped_valuelist) == 3:
                                if self.debug:
                                    self.debug_print(
                                    "the value with a keywords which is %s" % 
                                    tripped_valuelist[1])

                                filterters = tripped_valuelist[2].split("|")
                                for filterter in filterters:
                                    if self.debug:
                                        self.debug_print(
                                        "the filterter we will filt the \
                                        temp_list is %s" % filterter)

                                    if re.findall(filterter, str(caselist)):
                                        self.add_option_value(
                                            caselist,
                                            casename,
                                            tripped_optionname,
                                            tripped_valuename)
                                        break 
                                else:         
                                    filterter_list.append(caselist)
                            elif tripped_valuelist[1] == "no" and \
                                len(tripped_valuelist) == 2:
                                if self.debug:
                                    self.debug_print(
                                        "the value with a keywords \
                                         which is %s" % tripped_valuelist[1])

                                if re.findall(tripped_valuename, str(caselist)):
                                    f = lambda s: s.has_key(casename) == False
                                    temp_list = [filter(f, caselist)]
                            elif tripped_valuelist[1] == "no" and \
                                len(tripped_valuelist) == 3:
                                filterters = tripped_valuelist[2].split("|")
                                for filterter in filterters:
                                    if re.findall(filterter, str(caselist)):
                                        filterter_list.append(caselist)
                                        break
                                else:
                                    self.add_option_value(caselist, casename,
                                                          tripped_optionname,
                                                          tripped_valuename)
                            elif tripped_valuelist[1] == "include" and \
                                len(tripped_valuelist) == 2:
                                if re.findall(tripped_valuename, str(caselist)):
                                    self.add_option_value(caselist,
                                                          casename,
                                                          tripped_optionname,
                                                          tripped_valuename)
                                    temp_list = [caselist]
                        else:
                            self.add_option_value(caselist,
                                                  casename, 
                                                  tripped_optionname, 
                                                  tripped_valuename)

                        if self.debug:
                            self.debug_print(
                                "after parsing the caselist is %s" % 
                                 caselist)    
  
                    trash = [temp_list.remove(i) for i in filterter_list]

                    if self.debug:
                        self.debug_print(
                            "after handling the temp_list is %s" % 
                            temp_list) 

                    new_list += temp_list

        return new_list

    def parse(self, file, list):
        """ For the testcase name parsering. """ 
        while True:
            if self.debug:
                self.debug_print("the list is %s" % list)

            indent = self.get_next_line_indent(file)
            if indent < 0:
                break
            elif indent > 0 and indent == 4:
                if self.debug:
                    self.debug_print("we begin to parse the option line")
                list = self.option_parse(file, list, tripped_casename)
            else:
                casestring = self.get_next_line(file)

                tripped_caselist = casestring.strip().split()
                tripped_casename = tripped_caselist[0]

                if self.debug:
                    self.debug_print("we begin to handle the case : %s" %
                                     tripped_casename)

                if len(tripped_caselist) == 3 and \
                        tripped_caselist[1] == "times":
                    times = tripped_caselist[2]

                    if self.debug:
                        self.debug_print(
                            "the case with a keywords which is %s \
                             keywords_value is %s" %  
                            (tripped_caselist[1], times))

                    for i in range(int(times)):        
                        for caselist in list:
                            newdict = {}
                            newdict[tripped_casename] = {}
                            caselist.append(newdict)

                if tripped_casename == "options":
                    option_case = [{'options':{}}]
                    option_list = tripped_caselist[1:]
                    for option in option_list:
                        (optionkey, optionvalue) = option.split("=")
                        option_case[0]['options'][optionkey] = optionvalue
                    list.append(option_case)
                else:
                    for caselist in list:
                        newdict = {}
                        newdict[tripped_casename] = {}
                        caselist.append(newdict)

        return list

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        casefile = sys.argv[1]
    else:
        casefile = os.path.join(os.path.dirname(sys.argv[0]), "case.conf")
    list = config(casefile, debug=True).get_list()

    print "The number of generated list is %s" % len(list)
    print list

