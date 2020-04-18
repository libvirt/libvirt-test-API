import pytest
import os
import re
from  unittest.mock import Mock, MagicMock, patch
from libvirttestapi.utils import utils, process

class Cmd_Result():
    def __init__(self, exit_status, stderr, stdout):
        self.exit_status = exit_status
        self.stderr = stderr
        self.stdout = stdout


class TestUtils():
    def setup_method(self):
        self.mock_logger = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.error = Mock()

    @patch("libvirttestapi.utils.process.run")
    def test_hypervisor_kvm(self, mock_run):
        return_str = Cmd_Result(0, '', "pass" )
        mock_run.return_value = return_str
        result = utils.get_hypervisor()
        assert result == 'kvm'

    @patch("os.access")
    @patch("libvirttestapi.utils.process.run")
    def test_hypervisor_xen(self, mock_run, access_run):
        return_str = Cmd_Result(1, 'fail run', "fail" )
        mock_run.return_value = return_str
        access_run.return_value = True
        result = utils.get_hypervisor()
        assert result == 'xen'

    @patch("libvirttestapi.utils.utils.get_hypervisor")
    def test_geturi_kvm_local(self, mock_get_hypervisor):
        mock_get_hypervisor.return_value = 'kvm'
        result = utils.get_uri('127.0.0.1')
        assert result == "qemu:///system"

    @patch("libvirttestapi.utils.utils.get_hypervisor")
    def test_geturi_kvm_remote(self, mock_get_hypervisor):
        mock_get_hypervisor.return_value = 'kvm'
        result = utils.get_uri('192.168.122.8')
        assert result == "qemu+ssh://192.168.122.8/system"

    @patch("libvirttestapi.utils.process.run")
    def test_gethostarch(self, mock_run):
        return_str = Cmd_Result(0, '', 'x86_64 x86_64 GNU/Linux')
        mock_run.return_value = return_str
        result = utils.get_host_arch()
        assert result == 'x86_64'

    @patch("libvirttestapi.utils.process.run")
    def test_getlocalip(self, mock_run):
        return_str = Cmd_Result(0, '', 'xxxx:xxxx:xxxx 10.12.2.98')
        mock_run.return_value = return_str
        result = utils.get_local_ip()
        assert result == '10.12.2.98'

    @patch("libvirttestapi.utils.process.run")
    def test_getlocalip(self, mock_run):
        return_str = Cmd_Result(0, '', 'xxxx:xxxx:xxxx 10.12.2.98')
        mock_run.return_value = return_str
        result = utils.get_local_ip()
        assert result == '10.12.2.98'

    @patch("os.access")
    def test_gethostcpus_fail(self, mock_access):
        mock_access.return_value = False
        with pytest.raises(SystemExit):
             utils.get_host_cpus()

    @patch("libvirttestapi.utils.process.system_output")
    @patch("os.access")
    def test_gethostcpus(self, mock_access, mock_system_output):
        mock_access.return_value = True
        mock_system_output.return_value = 4
        result = utils.get_host_cpus()
        assert result == 4

    @patch("libvirttestapi.utils.process.system_output")
    @patch("os.access")
    @patch("libvirttestapi.utils.utils.isPower")
    def test_gethostfrequency(self, mock_isPower, mock_access, mock_system_output):
        mock_isPower.return_value = False
        mock_access.return_value = True
        mock_system_output.return_value = "cpu MHz		: 813.695"
        result = utils.get_host_frequency()
        assert result == '813.695'

    @patch("os.access")
    def test_gethostmemory_fail(self, mock_access):
        mock_access.return_value = False
        with pytest.raises(SystemExit):
             utils.get_host_memory()

    @patch("libvirttestapi.utils.process.system_output")
    @patch("os.access")
    def test_gethostmemory_pass(self, mock_access, mock_system_output):
        mock_access.return_value = True
        mock_system_output.return_value = 'MemTotal:       16166972 kB'
        result = utils.get_host_memory()
        assert result == 16166972

    def test_rand_str(self):
        result1 = utils.get_rand_str()
        result2 = utils.get_rand_str()
        assert result1 != result2

    @patch("os.system")
    @patch("libvirttestapi.utils.process.system_output")
    def test_stopselinux_enforcing(self, mock_system_output, mock_system):
        mock_system_output.return_value = "Enforcing"
        mock_system.return_value = True
        result = utils.stop_selinux()
        mock_system_output.assert_called_with("getenforce", shell=True, ignore_status=True)
        assert result == "Failed to stop selinux"

    @patch("os.system")
    @patch("libvirttestapi.utils.process.system_output")
    def test_stopselinux_permissive(self, mock_system_output, mock_system):
        mock_system_output.return_value = 'Permissive'
        result = utils.stop_selinux()
        assert result == "selinux is disabled"

    @patch("libvirttestapi.utils.process.run")
    def vtest_get_bridgeip_pass(self, mock_run):
        mock_run.return_value = Cmd_Result(0, 'success', '10.0.0.0/8 via 10.72.12.1 dev tun0 proto static metric 50')
        result = utils.get_bridge_ip('tun0')
        assert result == "10.72.12.1"

    @patch("os.path.isdir")
    @patch("libvirttestapi.utils.process.run")
    def test_setupnfs_fail(self, mock_run, mock_isdir):
        mock_isdir.return_value = False
        result = utils.setup_nfs('127.0.0.1', '/nfs', '/mnt', self.mock_logger)
        assert result == 1

    @patch("os.path.isdir")
    @patch("libvirttestapi.utils.process.run")
    def test_setupnfs_fail(self, mock_run, mock_isdir):
        mock_isdir.return_value = True
        mock_run.return_value = Cmd_Result(0, '', 'success run')
        result = utils.setup_nfs('127.0.0.1', '/nfs', '/mnt', self.mock_logger)
        assert result == 0

    @patch("libvirttestapi.utils.process.run")
    def test_cleannfs_pass(self, mock_run):
        mock_run.return_value = Cmd_Result(0, '', 'success run')
        result = utils.cleanup_nfs('/mnt', self.mock_logger)
        assert result == 0

    @patch("libvirttestapi.utils.process.run")
    def test_iscsi_login_pass(self, mock_run):
        mock_run.return_value = Cmd_Result(0, '', 'successful run')
        result = utils.iscsi_login('target', 'portal', self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.process.run")
    def test_iscsi_login_fail(self, mock_run):
        mock_run.return_value = Cmd_Result(1, 'fail', 'fail run')
        result = utils.iscsi_login('target', 'portal', self.mock_logger)
        assert result == False

    @patch("libvirttestapi.utils.process.run")
    def test_iscsi_login_pass(self, mock_run):
        mock_run.return_value = Cmd_Result(0, '', 'successful run')
        result = utils.iscsi_logout(self.mock_logger, 'target')
        assert result == True

    @patch("libvirttestapi.utils.process.run")
    def test_iscsi_get_sessions(self, mock_run):
        result_str = 'tcp: [2] 10.xx.xx.98:3260,1 iqn.2016-03.com.example:target (non-flash)'
        mock_run.return_value = Cmd_Result(0, '', result_str)
        result = utils.iscsi_get_sessions(self.mock_logger)
        assert result == [('10.xx.xx.98:3260', 'iqn.2016-03.com.example:target')]

    @patch("libvirttestapi.utils.utils.iscsi_get_sessions")
    def test_iscsi_is_login(self, mock_iscsi_get_sessions):
        result_str = [('10.xx.xx.98:3260', 'iqn.2016-03.com.example:target')]
        mock_iscsi_get_sessions.return_value = result_str
        result = utils.is_login('iqn.2016-03.com.example:target', self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.utils.is_login")
    def test_get_device_name_pass(self, mock_is_login, mock_run):
        result_str = '''Target: iqn.2016-03.com.example:target (non-flash)
                        scsi6 Channel 00 Id 0 Lun: 0
			Attached scsi disk sda		State: running
                     '''
        mock_is_login.return_value = True
        mock_run.return_value = Cmd_Result(0, '', result_str)
        result = utils.get_device_name('iqn.2016-03.com.example:target', self.mock_logger)
        assert result == '/dev/sda'

    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.utils.is_login")
    def test_get_device_name_Fail(self, mock_is_login, mock_run):
        mock_is_login.return_value = False
        result = utils.get_device_name('iqn.2016-03.com.example:target', self.mock_logger)
        assert result == ''

    @patch("os.path.exists")
    @patch("libvirttestapi.utils.utils.create_fs")
    @patch("libvirttestapi.utils.utils.create_partition")
    @patch("libvirttestapi.utils.utils.get_device_name")
    @patch("libvirttestapi.utils.utils.is_login")
    @patch("libvirttestapi.utils.utils.iscsi_discover")
    def test_setup_iscsi_pass(self, mock_iscsi_discover, mock_is_login, mock_get_device_name,
        mock_create_partition, mock_create_fs, mock_exists):
        mock_is_login.return_value = True
        mock_exists.return_value = False
        result = utils.setup_iscsi('127.0.0.1', 'iqn.2016-03.com.example:target', '/mnt', self.mock_logger)
        assert result == 0
