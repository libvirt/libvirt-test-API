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
# Summary: To generate a callable testcase function  
# Description: The module to initilize log module and match 
#              testcase function from proxy with corresponding 
#              argument to form a callable function.
# Maintainer: gren@redhat.com, ajia@redhat.com
# Updated: Oct 19 2009
# Version: 0.1.0

import time
import fcntl

import mapper
from utils.Python import log
from utils.Python import format

class FuncGen(object):
    """ to generate a callable testcase"""
    def __init__(self, cases_func_ref_dict,
                 activity, logfile,
                 testrunid, testid, 
                 log_xml_parser, lockfile, 
                 bugstxt):
        self.cases_func_ref_dict = cases_func_ref_dict
        self.logfile = logfile
        self.testrunid = testrunid
        self.testid = testid
        self.lockfile = lockfile
        self.bugstxt = bugstxt
        self.fmt = format.Format(logfile)
        self.log_xml_parser = log_xml_parser

        # save case information to a file in a format
        self.__case_info_save(activity, testrunid)

        mapper_obj = mapper.Mapper(activity)
        lan_pkg_tripped_cases, self.language = \
            mapper_obj.get_language_package_tripped()
        lan_tripped_cases = mapper_obj.get_language_tripped()

        for test_procedure in lan_tripped_cases:
            log_xml_parser.add_testprocedure_xml(testrunid, 
                                                 testid, 
                                                 test_procedure)
        
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
        retflag = self.generator()
        return retflag

    def bug_check(self, mod_func_name):
        """ check if there was already a bug in bugzilla assocaited with 
            specific testcase
        """
        exsited_bug = []
        bugstxt = open(self.bugstxt, "r")  
        linelist = bugstxt.readlines()

        if len(linelist) == 0:
            bugstxt.close()
            return exsited_bug
    
        for line in linelist:
            if line.startswith('#'):
                continue
            else:
                casename = line.split(' ', 1)[0]
                if casename == "casename:" + mod_func_name:
                    exsited_bug.append(line)
                else:
                    pass

        bugstxt.close()
        return exsited_bug   

    def generator(self):
        """ run each test case with the corresponding arguments and
            add log object into the dictionary of arguments
        """
        testcase_number = len(self.cases_ref_names)
        start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        retflag = 0

        for i in range(testcase_number):

            case_ref_name = self.cases_ref_names[i]
            self.fmt.printf('start', case_ref_name)
            case_params = self.cases_params_list[i]

            case_start_time = time.strftime("%Y-%m-%d %H:%M:%S")

            if self.language == 'Python':

                if case_ref_name != 'sleep':
                    case_params['logger'] = self.logger
                existed_bug_list = self.bug_check(case_ref_name)
                if len(existed_bug_list) == 0: 
                    if case_ref_name == 'sleep':
                        sleepsecs = case_params['sleep']
                        self.logger.info("sleep %s seconds" % sleepsecs)
                        time.sleep(int(sleepsecs))
                        ret = 0
                    else:
                        ret = self.cases_func_ref_dict[case_ref_name](case_params)
                else:
                    self.logger.info("about the testcase , bug existed:")
                    for existed_bug in existed_bug_list:
                        self.logger.info("%s" % existed_bug)

                    ret = 100
                    self.fmt.printf('end', case_ref_name, ret)
                    continue

            case_end_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            retflag += ret
            self.fmt.printf('end', case_ref_name, ret)

        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        result = (retflag and "FAIL") or "PASS"

        fcntl.lockf(self.lockfile.fileno(), fcntl.LOCK_EX)
        self.log_xml_parser.add_test_summary(self.testrunid, 
                                             self.testid, 
                                             result, 
                                             start_time, 
                                             end_time, 
                                             self.logfile)
        fcntl.lockf(self.lockfile.fileno(), fcntl.LOCK_UN)
        return retflag

    def __case_info_save(self, case, testrunid):
        """ save data of each test into a file under the testrunid directory 
            which the test belongs to
        """
        caseinfo_file = "log" + "/" + str(testrunid) + "/" + "caseinfo"
        CASEINFO = open(caseinfo_file, "a")
        CASEINFO.write(str(case) + "\n")
        CASEINFO.close()

