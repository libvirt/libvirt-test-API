import pytest
import os
from unittest.mock import Mock, MagicMock

from libvirttestapi.src import mapper
from libvirttestapi.src import exception as exc

class TestMapper():
    def setup_method(self):
        self.testcases_list = [{'test:test_case': {'foolname': 'bar'}}, {'clean': {'clean': 'yes'}}]

    def test_only_cleanup(self):
        testcases_list = [{'clean': {'clean': 'yes'}}]
        test_helper = mapper.Mapper(testcases_list)
        result_list = test_helper.module_casename_func_map()
        assert result_list == None

    def test_mapper_excute(self):
        test_helper = mapper.Mapper(self.testcases_list)
        result_list = test_helper.module_casename_func_map()
        assert result_list == [{'test:test_case:test_case:clean': {'foolname': 'bar'}}]
