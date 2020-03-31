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

import os
import sys
import time
import getopt
import shutil
import tempfile

from .src import parser
from .src import proxy
from .src import generator
from .src import env_clear
from .src import process
from .src import env_parser, env_inspect
from .utils import log, utils
from .utils.log import priorinit_logger
from .src.log_generator import LogGenerator
from .src.activityfilter import Filter
from .src.casecfgcheck import CaseCfgCheck


def usage():
    print("Usage: libvirt-test-api <OPTIONS> <ARGUMENTS>")
    print("\noptions: -h, --help : Display usage information"
          "\n         -c, --casefile: Specify configuration file"
          "\n         -t, --template: Print testcase config file template"
          "\n         -f, --logxml: Specify log file with type xml,"
          "\n                       defaults to log.xml in current directory"
          "\n         -l, --log-level: 0 or 1 or 2"
          "\n         -d, --delete-log: Delete log items"
          "\n         -m, --merge: Merge two log xmlfiles"
          "\n         -r, --rerun: Rerun one or more test")

    print("example:"
          "\n         libvirt-test-api -l 0|1|2 -c TEST.CONF"
          "\n         libvirt-test-api -c TEST.CONF -f TEST.XML"
          "\n         libvirt-test-api -t repos/domain/start.py ..."
          "\n         libvirt-test-api -m TESTONE.XML TESTTWO.XML"
          "\n         libvirt-test-api -d TEST.XML TESTRUNID TESTID"
          "\n         libvirt-test-api -d TEST.XML TESTRUNID"
          "\n         libvirt-test-api -d TEST.XML all"
          "\n         libvirt-test-api -f TEST.XML"
          "\n         libvirt-test-api -r TESTRUNID TESTID ...")


class Main(object):

    """ The class provides methods to run a new test and manage
        testing log and records
    """

    def __init__(self, casefile, logxml, loglevel):
        self.casefile = casefile
        self.logxml = logxml
        self.loglevel = loglevel

    def run(self, activities_options_list=None):
        """ Run a test instance """
        # generate testrunid from time point runing a testrun
        testrunid = time.strftime("%Y%m%d%H%M%S")
        while os.path.exists('log/%s' % testrunid):
            testrunid = str(int(testrunid) + 1)
        os.makedirs('log/%s' % testrunid)

        log_xml_parser = LogGenerator(self.logxml)

        # If the specified log xmlfile exists, then append the testrun
        # item of this time to the file, if not, create a new log xmlfile
        # named with the name and add the item
        if os.path.exists(self.logxml):
            log_xml_parser.add_testrun_xml(testrunid)
        else:
            log_xml_parser.generate_logxml()
            log_xml_parser.add_testrun_xml(testrunid)

        logfile = None
        logname = log.Log.get_log_name()
        if "AUTODIR" in os.environ:
            autotest_testdir = os.path.join(os.environ['AUTODIR'], 'tests/libvirt_test_API')
            logfile = os.path.join('%s/src/log/%s' % (autotest_testdir, testrunid), logname)
        else:
            logfile = os.path.join('log/%s' % testrunid, logname)
        envlog = log.EnvLog(logfile, self.loglevel)
        env_logger = envlog.env_log()
        caselog = log.CaseLog(logfile, self.loglevel)
        case_logger = caselog.case_log()
        start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        env_logger.info("\nStarted test at :%s", start_time)
        env_logger.info("    Log File: %s\n" % logfile)
        env_logger.info("Checking Testing Environment... ")
        base_path = utils.get_base_path()
        cfg_file = os.path.join(base_path, 'usr/share/libvirt-test-api/config', 'global.cfg')
        env = env_parser.Envparser(cfg_file)
        envck = env_inspect.EnvInspect(env, env_logger)
        if envck.env_checking() == 1:
            sys.exit(1)

        # if it's a new test, parsing the case configuration file to generate
        # a list of activities and options for the test instance.
        if activities_options_list is None:
            case_logger.debug('Parser the case configuration file to generate a data list')
            activities_options_list = parser.CaseFileParser(self.casefile, int(self.loglevel), case_logger).get_list()

        if "options" in activities_options_list[-1][0]:
            activities_list = activities_options_list[:-1]
            options_list = activities_options_list[-1]
        else:
            activities_list = activities_options_list
            options_list = [{'options': {}}]

        # multiply the activities list if option "times" given
        if "times" in options_list[0]['options']:
            times = int(options_list[0]['options']["times"])
            activities_list = activities_list * times

        filterobj = Filter(activities_list)

        unique_testcases = filterobj.unique_testcases()

        # __import__ TESTCASE.py once for duplicate testcase names
        proxy_obj = proxy.Proxy(unique_testcases)

        # check the options to each testcase in case config file
        casechk = CaseCfgCheck(proxy_obj, activities_list, case_logger)
        if casechk.check():
            return 1

        # get a list of unique testcase
        # with 'clean' flag appended to its previous testcase
        unique_testcase_keys = filterobj.unique_testcase_cleansuffix()
        cases_func_ref_dict = proxy_obj.get_func_call_dict(unique_testcase_keys)

        # get check function reference if that is defined in testcase file
        cases_checkfunc_ref_dict = proxy_obj.get_optionalfunc_call_dict('check')

        # create a null list, then, initilize generator to
        # get the callable testcase function
        # and put it into procs list for running.
        procs = []
        lockfile = tempfile.NamedTemporaryFile()
        testid = int(logname[-3:])-1
        for activity in activities_list:
            testid = testid+1
            log_xml_parser.add_test_xml(testrunid, str(testid))
            procs.append(generator.FuncGen(cases_func_ref_dict,
                                           cases_checkfunc_ref_dict,
                                           proxy_obj,
                                           activity, logfile,
                                           testrunid,
                                           testid,
                                           log_xml_parser,
                                           lockfile,
                                           env_logger, case_logger)
                         )

        totalnum = len(procs)
        passnum = 0
        failnum = 0
        testrunstart_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # if the value of option multiprocess is enable,
        # will call the module process to run the testcases
        # which stored in the list of procs, if disable,
        # will call them one by one
        if "multiprocess" in options_list[0]['options']:
            if options_list[0]['options']["multiprocess"] == "enable":
                proc = process.Process(procs)
                proc.fork()
                passnum, failnum = proc.wait()

            elif options_list[0]['options']["multiprocess"] == "disable":
                for i in procs:
                    ret = i()
                    if ret:
                        failnum += 1
                    else:
                        passnum += 1

        else:
            for i in procs:
                ret = i()
                if ret:
                    failnum += 1
                else:
                    passnum += 1

        testrunend_time = time.strftime("%Y-%m-%d %H:%M:%S")
        # close hypervisor connection
        envck.close_hypervisor_connection()
        # after running a testrun , add the summary of
        # the testrun in the format of xml into xmlfile
        log_xml_parser.add_testrun_summary(testrunid,
                                           passnum,
                                           failnum,
                                           totalnum,
                                           testrunstart_time,
                                           testrunend_time)

        lockfile.close()

        if "cleanup" in options_list[0]['options']:
            if options_list[0]['options']["cleanup"] == "enable":
                env_logger.info("Clean up Testing Environment...")
                cases_clearfunc_ref_dict = proxy_obj.get_optionalfunc_call_dict('clean')
                logname = log.Log.get_log_name()
                logfile = os.path.join('log/%s' % testrunid, logname)
                for activity in activities_list:
                    env_clear.EnvClear(cases_clearfunc_ref_dict, activity, logfile, self.loglevel)()
                env_logger.info("Done")
            elif options_list[0]['options']["cleanup"] == "disable":
                pass
            else:
                pass

        if failnum:
            return 1
        return 0

    def print_casefile(self, testcases):
        """print testcase file template"""
        modcasename = []
        for case in testcases:
            if not os.path.isfile(case) or not case.endswith('.py'):
                priorinit_logger.error("testcase %s couldn't be recognized" % case)
                return 1

            paths = case.split('/')
            modcasename.append(paths[1] + ':' + paths[2][:-3])

        proxy_obj = proxy.Proxy(modcasename)
        case_params = proxy_obj.get_params_variables()

        string = ("# the file is generated automatically, please\n"
                  "# make some modifications before the use of it\n"
                  "# params in [] are optional to its testcase\n")
        for key in modcasename:
            string += "%s\n" % key
            required_params, optional_params = case_params[key]
            for p in required_params:
                string += " " * 4 + p + "\n"
                string += " " * 8 + p.upper() + "\n"
            for p in optional_params:
                string += " " * 4 + "[" + p + "]\n"
                string += " " * 8 + str(optional_params[p]) + "\n"

            if proxy_obj.has_clean_function(key):
                string += "clean\n"

            string += "\n"

        priorinit_logger.info(string)
        return 0

    def remove_log(self, testrunid, testid=None):
        """  to remove log item in the log xmlfile """
        log_xml_parser = LogGenerator(self.logxml)

        # remove a test in a testrun
        if testrunid and testid:
            priorinit_logger.info("testrunid is %s" % testrunid)
            priorinit_logger.info("testid is %s" % testid)
            log_xml_parser.remove_test_xml(testrunid, testid)
            os.remove("log/%s/libvirt_test%s" % (testrunid, testid))
            priorinit_logger.info("Item testid %s in testrunid %s deleted successfully" %
                  (testid, testrunid))

        # delete all of records in a log xmlfile
        elif testrunid == "all" and not testid:
            testrunids = log_xml_parser.remove_alltestrun_xml()
            for testrunid in testrunids:
                shutil.rmtree("log/%s" % testrunid)
            priorinit_logger.info("All testruns deleted successfully")

        # delete record of a whole testrun
        elif testrunid.startswith("2") and not testid:
            priorinit_logger.info("testrunid is %s" % testrunid)
            log_xml_parser.remove_testrun_xml(testrunid)
            shutil.rmtree("log/%s" % testrunid)
            priorinit_logger.info("Testrun with testrunid %s deleted successfully" % testrunid)

        # report error if arguments given wrong
        else:
            priorinit_logger.info("Arguments error")
            usage()
            sys.exit(0)

    def merge_logxmls(self, logxml_two):
        """ to merge two log xml files of log into one"""
        log_xml_parser = LogGenerator(self.logxml)
        log_xml_parser.merge_xmlfiles(logxml_two)
        priorinit_logger.info("Merge the second log xml file %s to %s successfully " %
              (logxml_two, self.logxml))

    def rerun(self, testrunid, testid_list):
        """ rerun a specific test or a set of tests """
        caseinfo_file = "log" + "/" + str(testrunid) + "/" + "caseinfo"
        CASEINFO = open(caseinfo_file, "r")
        activities_list = []
        for testid in testid_list:
            activities = eval(CASEINFO.readlines()[testid - 1])
            activities_list.append(activities)

        self.run(activities_list)


def main():

    casefile = "./case.conf"
    logxml = "./log.xml"
    loglevel = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:tf:l:dmr",
                                   ["help", "casefile=", "template", "logxml=", "log-level=",
                                    "delete-log", "merge", "rerun"])
    except getopt.GetoptError as err:
        priorinit_logger.error(str(err))
        usage()
        sys.exit(2)

    for o, v in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-c" or o == "--casefile":
            casefile = v
        if o == "-t" or o == "--template":
            if len(args) <= 0:
                usage()
                sys.exit(1)
            maincase = Main('', '', '')
            if maincase.print_casefile(args):
                sys.exit(1)
            sys.exit(0)
        if o == "-f" or o == "--logxml":
            logxml = v
        if o == "-l" or o == "--log-level":
            loglevel = v
        if o == "-d" or o == "--delete-log":
            if len(args) == 1:
                usage()
                sys.exit(1)
            if len(args) == 2:
                logxml = args[0]
                testrunid = args[1]
                testid = None
            if len(args) == 3:
                logxml, testrunid, testid = args[0], args[1], args[2]
            if len(args) > 3:
                usage()
                sys.exit(1)

            maincase = Main(casefile, logxml, loglevel)
            maincase.remove_log(testrunid, testid)
            sys.exit(0)
        if o == "-m" or o == "--merge":
            if len(args) == 2:
                logxml_one = args[0]
                logxml_two = args[1]

                maincase = Main(casefile, logxml_one, loglevel)
                maincase.merge_logxmls(logxml_two)
                sys.exit(0)
            else:
                usage()
                sys.exit(1)
        if o == "-r" or o == "--rerun":
            if len(args) <= 1:
                usage()
                sys.exit(1)
            if len(args) >= 2:
                testid_list = []
                testrunid = args[0]
                for testid in args[1:]:
                    testid = int(testid)
                    testid_list.append(testid)
                maincase = Main(casefile, logxml, loglevel)
                maincase.rerun(testrunid, testid_list)
                sys.exit(0)

    maincase = Main(casefile, logxml, loglevel)
    if maincase.run():
        sys.exit(1)
    sys.exit(0)
