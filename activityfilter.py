#!/usr/bin/env python
#
#


class Filter(object):
    """filter activity list to form various data list"""
    def __init__(self, activities_list):
        self.testcase_keys = []
        for activity in activities_list:
            for testcase in activity:
                testcases_key = testcase.keys()
                self.testcase_keys += testcases_key

    def unique_testcase_cleansuffix(self):
        """get a list of module:testcase from activities_list
           eliminate duplicate items, with 'module:testcase_clean'
        """
        keylist_clean = self._keylist_cleanappended_without_sleep()
        return list(set(keylist_clean))

    def unique_testcases(self):
        """ get a list of module:testcase from activities_list
            eliminate duplicate items
        """
        keylist = self._keylist_without_sleep_clean()
        return list(set(keylist))

    def _keylist_without_sleep_clean(self):
        """ filter out 'clean' and 'sleep' flag
            to generate a list of testcases
        """
        keylist = []
        for key in self.testcase_keys:
            if key == 'clean' or key == 'sleep':
                continue

            keylist.append(key)

        return keylist

    def _keylist_cleanappended_without_sleep(self):
        """ remove 'sleep' flag, and append ':_clean' to
            the previous testcase to form a new element
        """
        keylist_clean = []
        prev_casename = ''

        for key in self.testcase_keys:
            if key == 'sleep':
                continue

            if key == 'clean':
                keylist_clean.append(prev_casename + ":_clean")
                continue

            prev_casename = key
            keylist_clean.append(prev_casename)

        return keylist_clean
