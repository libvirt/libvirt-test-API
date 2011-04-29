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
# This module matches the reference of clearing function from each testcase
# to the corresponding testcase's argument in the order of testcase running 
#
# Author: GuannanRen <gren@redhat.com>

import mapper
from utils.Python import log

class EnvClear(object):
    """ Generate a callable class of executing clearing function in
        each testcase.
    """
    def __init__(self, cases_clearfunc_ref_dict, activity, logfile, loglevel):
        self.cases_clearfunc_ref_dict = cases_clearfunc_ref_dict
        self.logfile = logfile
        self.loglevel = loglevel
  
        mapper_obj = mapper.Mapper(activity)
        pkg_tripped_cases = mapper_obj.get_package_tripped()

        self.cases_ref_names = []
        for case in pkg_tripped_cases:
            case_ref_name = case.keys()[0]
            self.cases_ref_names.append(case_ref_name)

        self.cases_params_list = []
        for case in pkg_tripped_cases:
            case_params = case.values()[0]
            self.cases_params_list.append(case_params)

    def __call__(self):
        retflag = self.envclear()
        return retflag

    def envclear(self):
        """ Run each clearing function with the corresponding arguments """
 
        envlog = log.EnvLog(self.logfile, self.loglevel)
        logger = envlog.env_log()
        
        testcase_number = len(self.cases_ref_names)

        for i in range(testcase_number):

            case_ref_name = self.cases_ref_names[i]
            case_params = self.cases_params_list[i]

            if case_ref_name == 'sleep':
                continue
            else:
                case_params['logger'] = logger
                self.cases_clearfunc_ref_dict[case_ref_name](case_params)

        del envlog

        return 0 
