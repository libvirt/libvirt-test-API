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
# Filename: envclear.py 
# Summary: To generate a callable class for clearing testing environment  
# Description: The module match the reference of clearing function 
#              from each testcase to the corresponding testcase's 
#              argument in the order of testcase running 
# Maintainer: gren@redhat.com
# Updated: Apr 04 2011
# Version: 0.1.0

import mapper
from utils.Python import log

class EnvClear(object):
    """ generate a callable class of executing 
        clearing function in each testcase
    """
    def __init__(self, cases_clearfunc_ref_dict, activity, logfile):
        self.cases_clearfunc_ref_dict = cases_clearfunc_ref_dict
        self.logfile = logfile
  
        mapper_obj = mapper.Mapper(activity)
        lan_pkg_tripped_cases, self.language = \
            mapper_obj.get_language_package_tripped()
        lan_tripped_cases = mapper_obj.get_language_tripped()

        if self.language == "Python":
            logs = log.Log(logfile)
            self.logger = logs.init_log()

        self.cases_ref_names = []
        for lan_tripped_case in lan_tripped_cases:
            case_ref_name = lan_tripped_case.keys()[0]
            self.cases_ref_names.append(case_ref_name)

        self.cases_params_list = []
        for lan_tripped_case in lan_tripped_cases:
            case_params = lan_tripped_case.values()[0]
            self.cases_params_list.append(case_params)

    def __call__(self):
        retflag = self.envclear()
        return retflag

    def envclear(self):
        """ run each clearing function with the corresponding arguments 
        """
        testcase_number = len(self.cases_ref_names)

        for i in range(testcase_number):

            case_ref_name = self.cases_ref_names[i]
            case_params = self.cases_params_list[i]

            if self.language == 'Python':
                if case_ref_name == 'sleep':
                    continue
                else:
                    case_params['logger'] = self.logger
                    self.cases_clearfunc_ref_dict[case_ref_name](case_params)
            else:
                pass

        return 0 


