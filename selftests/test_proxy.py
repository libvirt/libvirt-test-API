import pytest
from  unittest.mock import Mock, MagicMock, patch
from libvirttestapi.src import proxy
from libvirttestapi.src import exception as exc

class TestProxy():
    def setup_method(self):
        self.testcases_names = ['test:test_second', 'test:test_case']
        self.unique_testcase_keys = ['test:test_second', 'test:test_case', 'test:test_case:_clean']

    def test_get_funcall_pass(self):
        test_helper = proxy.Proxy(self.testcases_names)
        result = test_helper.get_func_call_dict(self.unique_testcase_keys)
        assert len(result.keys()) == 3
        assert 'test:test_case:test_case_clean' in result.keys()
        assert 'test:test_case:test_case' in result.keys()
        assert 'test:test_second:test_second' in result.keys()

    def test_get_variables_pass(self):
        test_helper = proxy.Proxy(self.testcases_names)
        result = test_helper.get_params_variables()
        assert result == {'test:test_second': [('foolname2',), {'optname2': 'secondfool'}], 'test:test_case': [('foolname',), {'optname': 'secondfool'}]}

    def test_testcase_params_pass(self):
        test_helper = proxy.Proxy(self.testcases_names)
        result = test_helper.get_testcase_params('test:test_case')
        assert result == [('foolname',), {'optname': 'secondfool'}]

    def test_testcase_params_None(self):
        test_helper = proxy.Proxy(self.testcases_names)
        result = test_helper.get_testcase_params(modcase='')
        assert result == None

    def test_get_has_clean(self):
        test_helper = proxy.Proxy(self.testcases_names)
        result = test_helper.has_clean_function('test:test_case')
        assert result == True

    def test_get_not_clean(self):
        test_helper = proxy.Proxy(self.testcases_names)
        result = test_helper.has_clean_function('test:test_send')
        assert result == False
