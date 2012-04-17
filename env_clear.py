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
#
# This module matches the reference of clearing function from each testcase
# to the corresponding testcase's argument in the order of testcase running
#

import mapper
from utils import log

class EnvClear(object):
    """ Generate a callable class of executing clearing function in
        each testcase.
    """
    def __init__(self, cases_clearfunc_ref_dict, activity, logfile, loglevel):
        self.cases_clearfunc_ref_dict = cases_clearfunc_ref_dict
        self.logfile = logfile
        self.loglevel = loglevel

        mapper_obj = mapper.Mapper(activity)
        clean_pkg_casename_func = mapper_obj.module_casename_cleanfunc_map()

        self.cases_ref_names = []
        for case in clean_pkg_casename_func:
            case_ref_name = case.keys()[0]
            self.cases_ref_names.append(case_ref_name)

        self.cases_params_list = []
        for case in clean_pkg_casename_func:
            case_params = case.values()[0]
            self.cases_params_list.append(case_params)

    def __call__(self):
        retflag = self.env_clear()
        return retflag

    def env_clear(self):
        """ Run each clean function with the corresponding arguments """

        envlog = log.EnvLog(self.logfile, self.loglevel)
        logger = envlog.env_log()

        testcase_number = len(self.cases_ref_names)

        for i in range(testcase_number):

            case_ref_name = self.cases_ref_names[i]
            case_params = self.cases_params_list[i]

            case_params['logger'] = logger
            if self.cases_clearfunc_ref_dict.has_key(case_ref_name):
                self.cases_clearfunc_ref_dict[case_ref_name](case_params)

        return 0
