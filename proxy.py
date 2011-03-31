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
# Filename: proxy.py
# Summary: Libvirt-test-API use it to generate a list of callable 
#          function reference.
# Description: The proxy examines the list of unique test cases, 
#              received from the generator and import each test case
#              from appropriate module directory.
# Maintainer: ajia@redhat.com
# Update: Oct 23, 2009
# Version: 0.1.0

class Proxy(object):
    """ The Proxy class is used for getting real function 
        call reference
    """
    def __init__(self, testcases_names):
        """ Argument case_list is test case list """
        self.testcases_names = testcases_names
        self.func_dict = dict()

    def get_func_call_dict(self):
        """ Provides multiple programming language support. In fact, 
            it is a dispather, and will return real function reference
            dictionary
        """
        for testcase_name in self.testcases_names:
            # get programming language, package, casename
            language = testcase_name.split(":")[0]
            package = testcase_name.split(":")[1]
            casename = testcase_name.split(":")[2]
            # according to language kind to dispatch function
            funcs = getattr(self, "get_%s_call_dict" % language.lower())
            func_ref = None
            if language == 'Python':
                func_ref = funcs(language, package, casename)
            if language == 'Java':
                func_ref = funcs(language, package)
            if language == 'Ruby':
                func_ref = funcs(language, package)
            # construct function call dictionary
            key = package + ":" + casename
            self.func_dict[key] = func_ref
        return self.func_dict

    def get_python_call_dict(self, *args):
        """ Return python testing function reference dictionary """
        (language, package, casename) = args
        case_abs_path = '%s.%s.%s.%s' % ('repos', language, package, casename)
        # main function name is the same as casename here
        func = casename
        case_mod = __import__(case_abs_path)
        components = case_abs_path.split('.')
        # import recursively module
        for component in components[1:]:
            case_mod = getattr(case_mod, component)
        main_function_ref = getattr(case_mod, func)
        return main_function_ref
    
    def get_java_call_dict(self, *args):
        """ Return java testing function reference dictionary """
        pass

    def get_ruby_call_dict(self, *args):
        """ Return ruby testing function reference dictionary """
        pass

