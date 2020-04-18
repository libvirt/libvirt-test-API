import pytest
from  unittest.mock import Mock, MagicMock, patch
from libvirttestapi.utils import utils
from libvirttestapi.utils import process
from libvirttestapi.src import env_inspect

class Cmd_Result():
        def __init__(self, exit_status, stderr, stdout):
            self.exit_status = exit_status
            self.stderr = stderr
            self.stdout = stdout


class TestInputVerify():
    def setup_method(self):
        self.mock_logger = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.error = Mock()
        self.env_parser = Mock()

    @patch("libvirttestapi.utils.process.run")
    def test_checklibvirt_rpmexist(self, mock_run):
        return_str = Cmd_Result(1, 'fail run', "success" )
        mock_run.return_value = return_str
        env_inspect.check_libvirt(self.mock_logger)
        assert mock_run.call_count == 3

    @patch("libvirttestapi.utils.process.run")
    def test_checklibvirt_rpmabsent(self, mock_run):
        return_str = Cmd_Result(0, 'fail run', "success")
        mock_run.return_value = return_str
        env_inspect.check_libvirt(self.mock_logger)
        assert mock_run.call_count == 6

    @patch("libvirttestapi.src.env_inspect.hostinfo")
    @patch("libvirttestapi.src.env_inspect.check_libvirt")
    @patch("libvirttestapi.src.env_inspect.sharemod_init")
    def test_envcheck_hostinfo_fail(self, mock_sharemod_init, mock_check_libvirt, mock_hostinfo):
        mock_hostinfo.return_value = 1
        inspect_helper = env_inspect.EnvInspect(self.mock_logger, self.env_parser)
        result = inspect_helper.env_checking()
        assert result == 1
        assert mock_hostinfo.called == True
        assert mock_check_libvirt.called == False
        assert mock_sharemod_init.called == False

    @patch("libvirttestapi.src.env_inspect.hostinfo")
    @patch("libvirttestapi.src.env_inspect.check_libvirt")
    @patch("libvirttestapi.src.env_inspect.sharemod_init")
    def test_envcheck_pass(self, mock_sharemod_init, mock_check_libvirt, mock_hostinfo):
        mock_hostinfo.return_value = 0
        mock_check_libvirt.return_value = 0
        mock_sharemod_init.return_value = 0
        inspect_helper = env_inspect.EnvInspect(self.mock_logger, self.env_parser)
        result = inspect_helper.env_checking()
        assert result == 0
        assert mock_hostinfo.called == True
        assert mock_check_libvirt.called == True
        assert mock_sharemod_init.called == True

    @patch("libvirttestapi.src.env_inspect.hostinfo")
    @patch("libvirttestapi.src.env_inspect.check_libvirt")
    @patch("libvirttestapi.src.env_inspect.sharemod_init")
    def test_envcheck_libvirt_fail(self, mock_sharemod_init, mock_check_libvirt, mock_hostinfo):
        mock_hostinfo.return_value = 0
        mock_check_libvirt.return_value = 1
        inspect_helper = env_inspect.EnvInspect(self.mock_logger, self.env_parser)
        result = inspect_helper.env_checking()
        assert result == 1
        assert mock_hostinfo.called == True
        assert mock_check_libvirt.called == True
        assert mock_sharemod_init.called == False

    @patch("libvirttestapi.src.env_inspect.hostinfo")
    @patch("libvirttestapi.src.env_inspect.check_libvirt")
    @patch("libvirttestapi.src.env_inspect.sharemod_init")
    def test_envcheck_sharemod_fail(self, mock_sharemod_init, mock_check_libvirt, mock_hostinfo):
        mock_hostinfo.return_value = 0
        mock_check_libvirt.return_value = 0
        mock_sharemod_init.return_value = 1
        inspect_helper = env_inspect.EnvInspect(self.mock_logger, self.env_parser)
        result = inspect_helper.env_checking()
        assert result == 1
        assert mock_hostinfo.called == True
        assert mock_check_libvirt.called == True
        assert mock_sharemod_init.called == True
