import pytest
from  unittest.mock import Mock, MagicMock, patch

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import os

from libvirttestapi.src import exception as exc
from libvirttestapi.src import env_parser
from libvirttestapi.utils import utils

class TestEnvParser():
    def setup_method(self):
        base_path = utils.get_base_path()
        config_path = os.path.join(base_path, 'usr/share/libvirt-test-api', 'config/', 'global.cfg')
        self.configfile = config_path

    @patch.object(ConfigParser.ConfigParser, "has_section")
    def test_has_section_true(self, mock_has_section):
        mock_has_section.return_value = True
        test_parser = env_parser.Envparser(self.configfile)
        result = test_parser.has_section("section")
        assert result == True

    @patch.object(ConfigParser.ConfigParser, "has_section")
    def test_has_section_False(self,  mock_has_section):
        mock_has_section.return_value = False
        test_parser = env_parser.Envparser(self.configfile)
        result = test_parser.has_section("section")
        assert result == False

    @patch.object(ConfigParser.ConfigParser, "has_section")
    @patch.object(ConfigParser.ConfigParser, "has_option")
    def test_has_option_true(self, mock_has_option, mock_has_section):
        mock_has_section.return_value = True
        mock_has_option.return_value = True
        test_parser = env_parser.Envparser(self.configfile)
        result = test_parser.has_option("section", "option")
        assert result == True

    @patch.object(ConfigParser.ConfigParser, "has_section")
    @patch.object(ConfigParser.ConfigParser, "has_option")
    def test_has_option_False(self,  mock_has_option, mock_has_section):
        mock_has_section.return_value = True
        mock_has_option.return_value = False
        test_parser = env_parser.Envparser(self.configfile)
        result = test_parser.has_option("section", "option")
        assert result == False

    @patch.object(ConfigParser.ConfigParser, "has_section")
    @patch.object(ConfigParser.ConfigParser, "has_option")
    def test_has_option_notcalled(self, mock_has_option, mock_has_section):
        mock_has_section.return_value = False
        test_parser = env_parser.Envparser(self.configfile)
        with pytest.raises(exc.SectionDoesNotExist):
            test_parser.has_option("section", "option")

    @patch.object(env_parser.Envparser, "has_section")
    def test_addsection_nonexecute(self, mock_has_section):
        mock_has_section.return_value = True
        test_parser = env_parser.Envparser(self.configfile)
        with pytest.raises(exc.SectionExist):
            test_parser.add_section("section")

    @patch.object(ConfigParser.ConfigParser, "add_section")
    @patch.object(env_parser.Envparser, "has_section")
    def test_addsection_execute(self, mock_has_section, mock_add_section):
        test_parser = env_parser.Envparser(self.configfile)
        mock_has_section.return_value = False
        test_parser.add_section("section")
        assert mock_add_section.called == True

    @patch.object(env_parser.Envparser, "has_option")
    @patch.object(env_parser.Envparser, "has_section")
    def test_removeoption_nonexecute(self, mock_has_section, mock_has_option):
        mock_has_section.return_value = True
        mock_has_option.return_value = False
        test_parser = env_parser.Envparser(self.configfile)
        with pytest.raises(exc.OptionDoesNotExist):
            test_parser.remove_option("section", "option")

    @patch.object(ConfigParser.ConfigParser, "remove_option")
    @patch.object(env_parser.Envparser, "has_option")
    @patch.object(env_parser.Envparser, "has_section")
    def test_removeoption_execute(self, mock_has_section, mock_has_option, mock_remove_option):
        mock_has_section.return_value = True
        mock_has_option.return_value = True
        test_parser = env_parser.Envparser(self.configfile)
        test_parser.remove_option("section", "option")
        assert mock_remove_option.called == True

    @patch.object(ConfigParser.ConfigParser, "set")
    @patch.object(env_parser.Envparser, "has_option")
    @patch.object(env_parser.Envparser, "has_section")
    def test_setvalue_nonexecute(self, mock_has_section, mock_has_option, mock_set):
        mock_has_section.return_value = True
        mock_has_option.return_value = False
        test_parser = env_parser.Envparser(self.configfile)
        with pytest.raises(exc.OptionDoesNotExist):
            test_parser.set_value("section", "option", "value")

    @patch.object(ConfigParser.ConfigParser, "set")
    @patch.object(env_parser.Envparser, "has_option")
    @patch.object(env_parser.Envparser, "has_section")
    def test_setvalue_execute(self, mock_has_section, mock_has_option, mock_set):
        mock_has_section.return_value = True
        mock_has_option.return_value = True
        test_parser = env_parser.Envparser(self.configfile)
        test_parser.set_value("section", "option", "value")
        assert mock_set.called == True
