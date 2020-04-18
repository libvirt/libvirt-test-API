import pytest
import shutil
from  unittest.mock import Mock, MagicMock, patch
from libvirttestapi.utils import utils, process, nfs

class Cmd_Result():
        def __init__(self, exit_status, stderr, stdout):
            self.exit_status = exit_status
            self.stderr = stderr
            self.stdout = stdout


class TestNfs():
    def setup_method(self):
        self.nfs_path = '/nfs'
        self.mount_path = '/mnt'
        self.mock_logger = Mock()
        self.mock_logger.info = Mock()
        self.mock_logger.error = Mock()
        self.server_ip = '127.0.0.1'
        self.remote_ip = '192.168.1.9'
        self.username = 'root'
        self.password = 'test'

    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.process.run")
    def test_localnfsexport_fail(self, mock_run, mock_local_restart_service):
        return_str = Cmd_Result(1, 'fail run', "fail" )
        mock_run.return_value = return_str
        result = nfs.local_nfs_exported(self.nfs_path, self.mock_logger)
        assert result == False

    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.process.run")
    def test_localnfsexport_pass(self, mock_run, mock_local_restart_service):
        return_str = Cmd_Result(0, 'run', 'success')
        mock_run.return_value = return_str
        mock_local_restart_service = return_str
        result = nfs.local_nfs_exported(self.nfs_path, self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.process.run")
    def test_localnfsexport_fail_restart(self, mock_run, mock_local_restart_service):
        return_str = Cmd_Result(0, 'run', 'success' )
        result_str = Cmd_Result(1, 'fail run', 'fail')
        mock_run.return_value = return_str
        mock_local_restart_service = result_str
        result = nfs.local_nfs_exported(self.nfs_path, self.mock_logger)
        assert result == 1

    @patch("libvirttestapi.utils.process.run")
    def test_localnfsexportclean_fail(self, mock_run):
        return_str = Cmd_Result(1, 'fail run', 'fail')
        mock_run.return_value = return_str
        result = nfs.local_nfs_exported_clean(self.nfs_path, self.mock_logger)
        assert result == False

    @patch("libvirttestapi.utils.process.run")
    def test_localnfsexportclean_pass(self, mock_run):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        result = nfs.local_nfs_exported_clean(self.nfs_path, self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.utils.Is_Fedora")
    @patch("libvirttestapi.utils.process.run")
    def test_localrestartservice_pass(self, mock_run, mock_Is_Fedora):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_Is_Fedora.return_value = True
        result = nfs.local_restart_service(self.mock_logger)
        mock_run.assert_called_with("systemctl restart rpcbind", shell=True, ignore_status=True)
        assert result == True

    @patch("libvirttestapi.utils.utils.isRelease")
    @patch("libvirttestapi.utils.utils.Is_Fedora")
    @patch("libvirttestapi.utils.process.run")
    def test_localrestartservice_callnfs(self, mock_run, mock_Is_Fedora, mock_isRelease):
        return_str = Cmd_Result(1, 'fail run', 'fail')
        mock_run.return_value = return_str
        mock_Is_Fedora.return_value = False
        mock_isRelease.return_value = False
        result = nfs.local_restart_service(self.mock_logger)
        mock_run.assert_called_with("systemctl restart nfs", shell=True, ignore_status=True)
        assert result == False

    @patch("libvirttestapi.utils.process.system_output")
    def test_local_is_mountd(self, mock_system_output):
        mount_line = "%s %s\n"%(self.nfs_path, self.mount_path)
        mock_system_output.return_value = mount_line
        result = nfs.local_is_mounted(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.process.system_output")
    def test_local_not_mountd(self, mock_system_output):
        mount_line = "sysfs /sys\n"
        mock_system_output.return_value = mount_line
        result = nfs.local_is_mounted(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == False

    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_umount")
    @patch("libvirttestapi.utils.nfs.local_is_mounted")
    def test_local_unmount_call(self, mock_local_is_mounted, mock_local_umount, mock_run):
        mock_local_is_mounted.return_value = True
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        nfs.local_mount(self.nfs_path, self.mount_path, self.mock_logger)
        assert mock_local_umount.called == True

    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_is_mounted")
    def test_local_mount_fail(self, mock_local_is_mounted, mock_run):
        return_str = Cmd_Result(1, 'fail run', 'fail')
        mock_run.return_value = return_str
        mock_local_is_mounted.return_value = False
        result = nfs.local_mount(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == False

    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_is_mounted")
    def test_local_mount_pass(self, mock_local_is_mounted, mock_run, mock_local_restart_service):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_local_is_mounted.return_value = False
        result = nfs.local_mount(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True

    @patch("os.path.isdir")
    @patch("os.path.exists")
    @patch("libvirttestapi.utils.nfs.local_mount")
    @patch("libvirttestapi.utils.nfs.local_nfs_exported")
    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.nfs.local_is_mounted")
    def test_localnfsetup_pass(self, mock_local_is_mounted, mock_local_restart_service,
        mock_local_nfs_exported, mock_local_mount, mock_exists, mock_isdir):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_local_is_mounted.return_value = True
        mock_local_restart_service.return_value = True
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_local_nfs_exported.return_value = True
        mock_local_mount.return_value = True
        result = nfs.local_nfs_setup(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True

    @patch("os.path.isdir")
    @patch("os.path.exists")
    @patch("libvirttestapi.utils.nfs.local_mount")
    @patch("libvirttestapi.utils.nfs.local_nfs_exported")
    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.nfs.local_is_mounted")
    def test_localnfsetup_nfsexported_false(self, mock_local_is_mounted, mock_local_restart_service,
        mock_local_nfs_exported, mock_local_mount, mock_exists, mock_isdir):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_local_is_mounted.return_value = True
        mock_local_restart_service.return_value = True
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_local_nfs_exported.return_value = False
        mock_local_mount.return_value = True
        result = nfs.local_nfs_setup(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True
        assert mock_local_mount.called == True

    @patch("os.path.isdir")
    @patch("os.path.exists")
    @patch("libvirttestapi.utils.nfs.local_mount")
    @patch("libvirttestapi.utils.nfs.local_nfs_exported")
    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.nfs.local_is_mounted")
    def test_localnfsetup_localmount_false(self, mock_local_is_mounted, mock_local_restart_service,
        mock_local_nfs_exported, mock_local_mount, mock_exists, mock_isdir):
        mock_local_is_mounted.return_value = True
        mock_local_restart_service.return_value = True
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_local_nfs_exported.return_value = True
        mock_local_mount.return_value = False
        result = nfs.local_nfs_setup(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True
        assert mock_local_mount.called == True

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("libvirttestapi.utils.nfs.local_nfs_exported_clean")
    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.nfs.local_umount")
    def test_localnfsclean_exportedclean_called(self, mock_local_umount, mock_local_restart_service,
        mock_local_nfs_exported_clean, mock_rmtree, mock_exists):
        mock_exists.return_value = True
        mock_local_umount.return_value = True
        mock_local_restart_service.return_value = True
        mock_local_nfs_exported_clean.return_value = True
        mock_rmtree.return_value = True
        result = nfs.local_nfs_clean(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True
        assert mock_local_nfs_exported_clean.called == True
        assert mock_rmtree.called == True

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("libvirttestapi.utils.nfs.local_nfs_exported_clean")
    @patch("libvirttestapi.utils.nfs.local_restart_service")
    @patch("libvirttestapi.utils.nfs.local_umount")
    def test_localnfsclean_exportedclean_noncalled(self, mock_local_umount, mock_local_restart_service,
        mock_local_nfs_exported_clean, mock_rmtree, mock_exists):
        mock_exists.return_value = False
        mock_local_umount.return_value = True
        mock_local_restart_service.return_value = True
        mock_local_nfs_exported_clean.return_value = True
        mock_rmtree.return_value = True
        result = nfs.local_nfs_clean(self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True
        assert mock_local_nfs_exported_clean.called == False
        assert mock_local_restart_service.called == True
        assert mock_rmtree.called == False

    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_nfs_setup")
    def test_nfsetup_remoteip_none(self, mock_local_nfs_setup, mock_run):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_local_nfs_setup.return_value = True
        remote_ip = None
        result = nfs.nfs_setup(self.server_ip, remote_ip, self.username,
                self.password, self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.utils.remote_exec_pexpect")
    @patch("libvirttestapi.utils.nfs.remote_mount")
    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_nfs_setup")
    def test_nfsetup_pass(self, mock_local_nfs_setup, mock_run,
        mock_remote_mount, mock_remote_exec_pexpect):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_local_nfs_setup.return_value = True
        mock_remote_mount.return_value = True
        mock_remote_exec_pexpect.return_value = (0, 'pass')
        result = nfs.nfs_setup(self.server_ip, self.remote_ip, self.username,
                self.password, self.nfs_path, self.mount_path, self.mock_logger)
        assert result == True

    @patch("libvirttestapi.utils.utils.remote_exec_pexpect")
    @patch("libvirttestapi.utils.nfs.remote_mount")
    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_nfs_setup")
    def test_nfsetup_remotemount_fail(self, mock_local_nfs_setup, mock_run,
        mock_remote_mount, mock_remote_exec_pexpect):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_local_nfs_setup.return_value = True
        mock_remote_mount.return_value = False
        mock_remote_exec_pexpect.return_value = (0, 'pass')
        result = nfs.nfs_setup(self.server_ip, self.remote_ip, self.username,
                self.password, self.nfs_path, self.mount_path, self.mock_logger)
        assert result == False
        assert mock_remote_exec_pexpect.called  == False

    @patch("libvirttestapi.utils.utils.remote_exec_pexpect")
    @patch("libvirttestapi.utils.nfs.remote_mount")
    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_nfs_setup")
    def test_nfsetup_remoteexec_fail(self, mock_local_nfs_setup, mock_run,
        mock_remote_mount, mock_remote_exec_pexpect):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_local_nfs_setup.return_value = True
        mock_remote_mount.return_value = False
        mock_remote_exec_pexpect.return_value = (1, 'Fail')
        result = nfs.nfs_setup(self.server_ip, self.remote_ip, self.username,
                self.password, self.nfs_path, self.mount_path, self.mock_logger)
        assert result == False

    @patch("libvirttestapi.utils.utils.remote_exec_pexpect")
    @patch("libvirttestapi.utils.nfs.remote_mount")
    @patch("libvirttestapi.utils.process.run")
    @patch("libvirttestapi.utils.nfs.local_nfs_setup")
    def test_nfsetup_localnfssetup_fail(self, mock_local_nfs_setup, mock_run,
        mock_remote_mount, mock_remote_exec_pexpect):
        return_str = Cmd_Result(0, 'run', 'pass')
        mock_run.return_value = return_str
        mock_local_nfs_setup.return_value = False
        result = nfs.nfs_setup(self.server_ip, self.remote_ip, self.username,
                self.password, self.nfs_path, self.mount_path, self.mock_logger)
        assert result == False
        assert mock_remote_exec_pexpect.called  == False
