#!/usr/bin/env python
#
#

import os
import sys
import time
import getopt
import shutil
import tempfile

import parser
import proxy
import generator
import env_clear
import process
from utils import log
from logxmlparser import LogXMLParser
from activityfilter import Filter
from casecfgcheck import CaseCfgCheck

def usage():
    print "Usage: libvirt_test_api.py <OPTIONS> <ARGUS>"
    print "\noptions: -h, --help : Display usage information \
           \n         -c, --casefile: Specify configuration file \
           \n         -t, --template: Print testcase config file template \
           \n         -f, --logxml: Specify log file with type xml \
           \n         -l, --log-level: 0 or 1 currently \
           \n         -d, --delete-log: Delete log items \
           \n         -m, --merge: Merge two log xmlfiles \
           \n         -r, --rerun: Rerun one or more test"


    print "example: \
           \n         python libvirt-test-api.py -l 0|1 -c TEST.CONF    \
           \n         python libvirt-test-api.py -c TEST.CONF -f TEST.XML \
           \n         python libvirt-test-api.py -t repos/domain/start.py ... \
           \n         python libvirt-test-api.py -m TESTONE.XML TESTTWO.XML \
           \n         python libvirt-test-api.py -d TEST.XML TESTRUNID TESTID \
           \n         python libvirt-test-api.py -d TEST.XML TESTRUNID \
           \n         python libvirt-test-api.py -d TEST.XML all \
           \n         python libvirt-test-api.py -f TEST.XML \
-r TESTRUNID TESTID ..."

def append_path():
    """Append root path of package"""
    pwd = os.getcwd()
    if pwd in sys.path:
        pass
    else:
        sys.path.append(pwd)

class Main(object):
    """ The class provides methods to run a new test and manage
        testing log and records
    """
    def __init__(self, casefile, logxml, loglevel, bugstxt):
        self.casefile = casefile
        self.logxml = logxml
        self.loglevel = loglevel
        self.bugstxt = bugstxt

    def run(self, activities_options_list=None):
        """ Run a test instance """

        # if it's a new test, parsing the case configuration file to generate
        # a list of activities and options for the test instance.
        if activities_options_list == None:
            activities_options_list = \
                parser.CaseFileParser(self.casefile).get_list()

        if activities_options_list[-1][0].has_key("options"):
            activities_list = activities_options_list[:-1]
            options_list = activities_options_list[-1]
        else:
            activities_list = activities_options_list
            options_list = [{'options':{}}]

        # generate testrunid from time point runing a testrun
        testrunid = time.strftime("%Y%m%d%H%M%S")
        os.makedirs('log/%s' %testrunid)

        log_xml_parser = LogXMLParser(self.logxml)

        # If the specified log xmlfile exists, then append the testrun
        # item of this time to the file, if not, create a new log xmlfile
        # named with the name and add the item
        if os.path.exists(self.logxml):
            log_xml_parser.add_testrun_xml(testrunid)
        else:
            log_xml_parser.generate_logxml()
            log_xml_parser.add_testrun_xml(testrunid)

        # multiply the activities list if option "times" given
        if options_list[0]['options'].has_key("times"):
            times = int(options_list[0]['options']["times"])
            activities_list = activities_list * times

        filterobj = Filter(activities_list)

        unique_testcases = filterobj.unique_testcases()

        # __import__ TESTCASE.py once for duplicate testcase names
        proxy_obj = proxy.Proxy(unique_testcases)

        # check the options to each testcase in case config file
        casechk = CaseCfgCheck(proxy_obj, activities_list)
        if casechk.check():
            return 1

        # get a list of unique testcase
        # with 'clean' flag appended to its previous testcase
        unique_testcase_keys = filterobj.unique_testcase_cleansuffix()
        cases_func_ref_dict = proxy_obj.get_func_call_dict(unique_testcase_keys)

        # create a null list, then, initilize generator to
        # get the callable testcase function
        # and put it into procs list for running.
        procs = []
        lockfile = tempfile.NamedTemporaryFile()
        logfile = None

        for activity in activities_list:
            logname = log.Log.get_log_name()
            testid = logname[-3:]
            log_xml_parser.add_test_xml(testrunid, testid)
            if os.environ.has_key('AUTODIR'):
                autotest_testdir = os.path.join(os.environ['AUTODIR'],'tests/libvirt_test_API')
                logfile = os.path.join('%s/libvirt-test-API/log/%s' % (autotest_testdir, testrunid), logname)
            else:
                logfile = os.path.join('log/%s' % testrunid, logname)
            procs.append(generator.FuncGen(cases_func_ref_dict,
                                           activity,
                                           logfile,
                                           testrunid,
                                           testid,
                                           log_xml_parser,
                                           lockfile,
                                           self.bugstxt,
                                           self.loglevel)
                        )

        totalnum = len(procs)
        passnum = 0
        failnum = 0
        testrunstart_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # if the value of option multiprocess is enable,
        # will call the module process to run the testcases
	# which stored in the list of procs, if disable,
	# will call them one by one
        if options_list[0]['options'].has_key("multiprocess"):
            if  options_list[0]['options']["multiprocess"] == "enable":
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

        # after running a testrun , add the summary of
        # the testrun in the format of xml into xmlfile
        log_xml_parser.add_testrun_summary(testrunid,
                                           passnum,
                                           failnum,
                                           totalnum,
                                           testrunstart_time,
                                           testrunend_time)

        lockfile.close()

        if options_list[0]['options'].has_key("cleanup"):
            if options_list[0]['options']["cleanup"] == "enable":
                print "Clean up Testing Environment..."
                cases_clearfunc_ref_dict = proxy_obj.get_clearfunc_call_dict()
                log.Log.counter = 0
                for activity in activities_list:
                    logname = log.Log.get_log_name()
                    logfile = os.path.join('log/%s' % testrunid, logname)
                    env_clear.EnvClear(cases_clearfunc_ref_dict, activity, logfile, self.loglevel)()
                print "Done"
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
                print "testcase %s couldn't be recognized" % case
                return 1

            paths = case.split('/')
            modcasename.append(paths[1] + ':' + paths[2][:-3])

        proxy_obj = proxy.Proxy(modcasename)
        case_params = proxy_obj.get_params_variables()

        string = "# the file is generated automatically, please\n" \
                 "# make some modifications before the use of it\n" \
                 "# params in [] are optional to its testcase\n"
        for key in modcasename:
            string += "%s\n" % key
            required_params, optional_params = case_params[key]
            for p in required_params:
                string += " " * 4  + p + "\n"
                string += " " * 8 + p.upper() + "\n"
            for p in optional_params:
                string += " " * 4 + "[" + p + "]\n"
                string += " " * 8 + p.upper() + "\n"

            if proxy_obj.has_clean_function(key):
                string += "clean\n"

            string += "\n"

        print string
        return 0

    def remove_log(self, testrunid, testid = None):
        """  to remove log item in the log xmlfile """
        log_xml_parser = LogXMLParser(self.logxml)

        # remove a test in a testrun
        if testrunid and testid:
            print "testrunid is %s" % testrunid
            print "testid is %s" % testid
            log_xml_parser.remove_test_xml(testrunid, testid)
            os.remove("log/%s/libvirt_test%s" % (testrunid, testid))
            print "Item testid %s in testrunid %s deleted successfully" % \
                  (testid, testrunid)

        # delete all of records in a log xmlfile
        elif testrunid == "all" and not testid:
            testrunids = log_xml_parser.remove_alltestrun_xml()
            for testrunid in testrunids:
                shutil.rmtree("log/%s" % testrunid)
            print "All testruns deleted successfully"

        # delete record of a whole testrun
        elif testrunid.startswith("2") and not testid:
            print "testrunid is %s" % testrunid
            log_xml_parser.remove_testrun_xml(testrunid)
            shutil.rmtree("log/%s" % testrunid)
            print "Testrun with testrunid %s deleted successfully" % testrunid

        # report error if arguments given wrong
        else:
            print "Arguments error"
            usage()
            sys.exit(0)

    def merge_logxmls(self, logxml_two):
        """ to merge two log xml files of log into one"""
        log_xml_parser = LogXMLParser(self.logxml)
        log_xml_parser.merge_xmlfiles(logxml_two)
        print "Merge the second log xml file %s to %s successfully " % \
              (logxml_two, self.logxml)

    def rerun(self, testrunid, testid_list):
        """ rerun a specific test or a set of tests """
        caseinfo_file = "log" + "/" + str(testrunid) + "/" + "caseinfo"
        CASEINFO = open(caseinfo_file, "r")
        activities_list = []
        for testid in testid_list:
            activities = eval(CASEINFO.readlines()[testid-1])
            activities_list.append(activites)

        self.run(activities_list)

if __name__ == "__main__":

    casefile = "./case.conf"
    logxml = "./log.xml"
    bugstxt = "./BUGSKIP"
    loglevel = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:tl:dmr",
                    ["help", "casefile=", "template", "logxml=",
                    "delete-log=", "merge=", "rerun="])
    except getopt.GetoptError, err:
        print str(err)
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
            main = Main('', '', '', '')
            if main.print_casefile(args):
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

            main = Main(casefile, logxml, loglevel, bugstxt)
            main.remove_log(testrunid, testid)
            sys.exit(0)
        if o == "-m" or o == "--merge":
            if len(args) == 2:
                logxml_one = args[0]
                logxml_two = args[1]

                main = Main(casefile, logxml_one, loglevel, bugstxt)
                main.merge_logxmls(logxml_two)
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
                main = Main(casefile, logxml, loglevel, bugstxt)
                main.rerun(testrunid, testid_list)
                sys.exit(0)

    # Add root path of libvirt-test-API into sys.path
    append_path()

    main = Main(casefile, logxml, loglevel, bugstxt)
    if main.run():
        sys.exit(1)
    sys.exit(0)
