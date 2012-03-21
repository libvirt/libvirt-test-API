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
# Generate a list of callable function references.

# The proxy examines the list of unique test cases, received from the
# generator and import each test case from appropriate module directory.

import exception


class Proxy(object):
    """ The Proxy class is used for getting real function call reference """

    def __init__(self, testcases_names):
        """ Argument case_list is test case list """
        self.testcases_names = testcases_names

    def get_func_call_dict(self):
        """Return running function reference dictionary """
        self.func_dict = dict()
        for testcase_name in self.testcases_names:
            # Get programming package, casename
            elements = testcase_name.split(":")
            package = elements[0]
            casename = elements[1]
            func = casename

            if len(elements) == 3:
                keyword = elements[2]
                func = casename + keyword

            # Dispatch functions
            funcs = getattr(self, "get_call_dict")
            func_ref = None
            func_ref = funcs(package, casename, func)

            # Construct function call dictionary
            key = package + ":" + casename + ":" + func
            self.func_dict[key] = func_ref
        return self.func_dict

    def get_clearfunc_call_dict(self):
        """ Return a clearing function reference dictionary. """
        self.func_dict = dict()
        for testcase_name in self.testcases_names:
            # Get programming package, casename
            elements = testcase_name.split(":")

            if len(elements) == 3:
                continue

            package = testcase_name.split(":")[0]
            casename = testcase_name.split(":")[1]

            # According to language kind to dispatch function
            funcs = getattr(self, "get_call_dict")
            func_ref = None
            func = casename + "_clean"

            func_ref = funcs(package, casename, func)

            # Construct function call dictionary
            key = package + ":" + casename + ":" + func
            self.func_dict[key] = func_ref
        return self.func_dict

    def get_call_dict(self, *args):
        """ Return testing function reference dictionary """
        (package, casename, func) = args
        case_abs_path = '%s.%s.%s' % ('repos', package, casename)

        # Main function name is the same as casename here
        case_mod = __import__(case_abs_path)
        components = case_abs_path.split('.')

        # Import recursively module
        for component in components[1:]:
            if component == "":
                raise exception.CaseConfigfileError("Missing module name after \":\"")
            case_mod = getattr(case_mod, component)
        main_function_ref = getattr(case_mod, func)
        return main_function_ref

