import pytest
from  unittest.mock import Mock, MagicMock, patch
from libvirttestapi.utils import utils, sriov

class Cmd_Result():
        def __init__(self, exit_status, stderr, stdout):
            self.exit_status = exit_status
            self.stderr = stderr
            self.stdout = stdout


class TestSriov():
    def setup_method(self):
        self.mock_logger = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.error = Mock()
        self.DRIVERS_LIST = ['ixgbe', 'igb']

    @patch("libvirttestapi.utils.process.run")
    def test_getdrivername_none(self, mock_run):
        return_str = Cmd_Result(1, 'fail', 'fail run')
        mock_run.return_value = return_str
        result = sriov.get_driver_name(self.mock_logger)
        assert result == ''

    @patch("libvirttestapi.utils.process.run")
    def test_getdrivername_ixgbe(self, mock_run):
        return_str = Cmd_Result(0, '', 'sucess')
        mock_run.return_value = return_str
        result = sriov.get_driver_name(self.mock_logger)
        assert result == 'ixgbe'
