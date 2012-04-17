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
# Generate a list of callable function references.

# The proxy examines the list of unique test cases, received from the
# generator and import each test case from appropriate module directory.

import exception

class Proxy(object):
    """ The Proxy class is used for getting real function call reference """

    def __init__(self, testcases_names):
        """ Argument case_list is test case list """
        self.testcases_names = testcases_names
        self.testcase_ref_dict = {}

        for testcase_name in self.testcases_names:
            elements = testcase_name.split(':')

            # we just want to __import__ testcase.py
            # so ignore the rest of elements in the list
            module = elements[0]
            casename = elements[1]

            casemod_ref = self.get_call_dict(module, casename)
            modcase = module + ':' + casename
            self.testcase_ref_dict[modcase] = casemod_ref

    def get_func_call_dict(self, unique_testcase_keys):
        """get reference to functions defined in testcase file """
        func_dict = {}
        for testcase_name in unique_testcase_keys:
            # Get module, casename
            elements = testcase_name.split(':')
            module = elements[0]
            casename = elements[1]
            func = casename

            if len(elements) == 3:
                # flag is like "_clean" in testcases_names
                # this func is for _clean function in testcase
                flag = elements[2]
                func = casename + flag

            # use modcase key to get the reference to corresponding
            # testcase module
            modcase = module + ':' + casename
            casemod_ref = self.testcase_ref_dict[modcase]
            var_func_names = dir(casemod_ref)

            key = modcase + ':' + func
            # check if the expected function is present in
            # the list of string name from dir()
            if func in var_func_names:
                func_ref = getattr(casemod_ref, func)
                func_dict[key] = func_ref
            else:
                raise exception.TestCaseError("function %s not found in %s" % \
                                              (func, modcase))
        return func_dict

    def get_clearfunc_call_dict(self):
        """ Return a clearing function reference dictionary. """
        func_dict = {}
        for testcase_name in self.testcases_names:
            # Get module, casename
            elements = testcase_name.split(':')

            if len(elements) == 3:
                continue

            module = elements[0]
            casename = elements[1]
            func = casename + '_clean'

            casemod_ref = self.testcase_ref_dict[testcase_name]
            var_func_names = dir(casemod_ref)

            key = module + ':' + casename + ':' + func

            # the clean function is optional, we get its reference
            # only if it exists in testcases
            if func in var_func_names:
                func_ref = getattr(casemod_ref, func)
                func_dict[key] = func_ref

        return func_dict

    def get_params_variables(self):
        """ Return the reference to global variable 'required_params'
            in testcase
        """
        case_params = {}
        for testcase_name in self.testcases_names:
            elements = testcase_name.split(':')

            if len(elements) == 3:
                continue

            module = elements[0]
            casename = elements[1]

            casemod_ref = self.testcase_ref_dict[testcase_name]
            var_func_names = dir(casemod_ref)

            if 'required_params' in var_func_names \
               and 'optional_params' in var_func_names:
                case_params[testcase_name] = \
                    [casemod_ref.required_params, casemod_ref.optional_params]
            else:
                raise exception.TestCaseError\
                      ("required_params or optional_params not found in %s" % testcase_name)
        return case_params

    def has_clean_function(self, testcase_name):
        """ Return true if the testcase have clean function
        """
        if testcase_name not in self.testcases_names:
            return False

        elements = testcase_name.split(':')
        casename = elements[1]
        func = casename + '_clean'

        casemod_ref = self.testcase_ref_dict[testcase_name]
        var_func_names = dir(casemod_ref)

        if func in var_func_names:
            return True
        return False

    def get_call_dict(self, module, casename, func = None):
        """ Return testing function reference dictionary """
        case_abs_path = '%s.%s.%s' % ('repos', module, casename)

        # import tescase file
        casemod_ref = __import__(case_abs_path)
        components = case_abs_path.split('.')

        # Import recursively module
        for component in components[1:]:
            casemod_ref = getattr(casemod_ref, component)

        if func:
            main_function_ref = getattr(casemod_ref, func)
            return main_function_ref

        return casemod_ref
