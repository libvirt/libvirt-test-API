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
# This module to initilize log module and match testcase function from
# proxy with corresponding argument to form a callable function.

import time
import fcntl
import sys
import os
import traceback

import mapper
from utils import log
from utils import format
from utils import env_parser

# Import of distribution-specific code.  If this is needed somewhere
# else in the future, please don't copy-paste this, but create some
# sensible distribution-specific package
for dist in os.listdir('dist'):
    if os.path.exists('/etc/%s-release' % dist):
        exec('from dist.%s import env_inspect' % dist)
        break

class FuncGen(object):
    """ To generate a callable testcase"""
    def __init__(self, cases_func_ref_dict,
                 activity, logfile,
                 testrunid, testid,
                 log_xml_parser, lockfile,
                 bugstxt, loglevel):
        self.cases_func_ref_dict = cases_func_ref_dict
        self.logfile = logfile
        self.testrunid = testrunid
        self.testid = testid
        self.lockfile = lockfile
        self.bugstxt = bugstxt
        self.loglevel = loglevel
        self.testcase_number = 0

        self.fmt = format.Format(logfile)
        self.log_xml_parser = log_xml_parser

        # Save case information to a file in a format
        self.__case_info_save(activity, testrunid)

        self.env = env_parser.Envparser("env.cfg")

        mapper_obj = mapper.Mapper(activity)
        pkg_casename_func = mapper_obj.module_casename_func_map()

        for test_procedure in pkg_casename_func:
            log_xml_parser.add_testprocedure_xml(testrunid,
                                                 testid,
                                                 test_procedure)
        self.cases_ref_names = []
        for case in pkg_casename_func:
            case_ref_name = case.keys()[0]
            if case_ref_name[-6:] != "_clean":
                self.testcase_number += 1
            self.cases_ref_names.append(case_ref_name)

        self.cases_params_list = []
        for case in pkg_casename_func:
            case_params = case.values()[0]
            self.cases_params_list.append(case_params)

    def __call__(self):
        retflag = self.generator()
        return retflag

    def bug_check(self, mod_func_name):
        """ Check if there was already a bug in bugzilla assocaited with
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
        """ Run each test case with the corresponding arguments and
            add log object into the dictionary of arguments
        """

        envlog = log.EnvLog(self.logfile, self.loglevel)
        env_logger = envlog.env_log()
        loop_number = len(self.cases_ref_names)
        start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        env_logger.info("Checking Testing Environment... ")
        envck = env_inspect.EnvInspect(self.env, env_logger)

        if envck.env_checking() == 1:
            sys.exit(1)
        else:
            env_logger.info("\nStart Testing:")
            env_logger.info("    Case Count: %s" % self.testcase_number)
            env_logger.info("    Log File: %s\n" % self.logfile)

        caselog = log.CaseLog(self.logfile, self.loglevel)
        case_logger = caselog.case_log()

        retflag = 0
        for i in range(loop_number):

            case_ref_name = self.cases_ref_names[i]
            pkg_casename = case_ref_name.rsplit(":", 1)[0]
            funcname = case_ref_name.rsplit(":", 1)[-1]

            if "_clean" not in funcname:
                cleanoper = 0
            else:
                cleanoper = 1


            if not cleanoper:
                self.fmt.print_start(pkg_casename, env_logger)
            else:
                self.fmt.print_string(12*" " + "Cleaning...", env_logger)

            case_params = self.cases_params_list[i]

            case_start_time = time.strftime("%Y-%m-%d %H:%M:%S")

            ret = -1
            clean_ret = -1
            try:
                try:
                    if case_ref_name != 'sleep':
                        case_params['logger'] = case_logger

                    existed_bug_list = self.bug_check(pkg_casename)

                    if len(existed_bug_list) == 0:
                        if case_ref_name == 'sleep':
                            sleepsecs = case_params['sleep']
                            case_logger.info("sleep %s seconds" % sleepsecs)
                            time.sleep(int(sleepsecs))
                            ret = 0
                        else:
                            ret = self.cases_func_ref_dict[case_ref_name](case_params)
                            if cleanoper:
                                clean_ret = ret
                                ret = 0
                    else:
                        case_logger.info("about the testcase , bug existed:")
                        for existed_bug in existed_bug_list:
                            case_logger.info("%s" % existed_bug)

                        ret = 100
                        self.fmt.print_end(pkg_casename, ret, env_logger)
                        continue
                except Exception, e:
                    case_logger.error(traceback.format_exc())
                    continue
            finally:
                case_end_time = time.strftime("%Y-%m-%d %H:%M:%S")
                if ret == -1:
                    ret = 1
                elif ret == 100:
                    retflag += 0
                else:
                    pass
                retflag += ret

                if not cleanoper:
                    self.fmt.print_end(pkg_casename, ret, env_logger)
                else:
                    if clean_ret < 1:
                        self.fmt.print_string(21*" " + "Done", env_logger)
                    else:
                        self.fmt.print_string(21*" " + "Fail", env_logger)

        # close hypervisor connection
        envck.close_hypervisor_connection()
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")

        env_logger.info("\nSummary:")
        env_logger.info("    Total:%s [Pass:%s Fail:%s]" % \
                     (self.testcase_number, (self.testcase_number - retflag), retflag))

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
        """ Save data of each test into a file under the testrunid directory
            which the test belongs to.
        """
        caseinfo_file = "log" + "/" + str(testrunid) + "/" + "caseinfo"
        CASEINFO = open(caseinfo_file, "a")
        CASEINFO.write(str(case) + "\n")
        CASEINFO.close()
