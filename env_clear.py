#!/usr/bin/env python
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
