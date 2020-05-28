import pytest
import os
from unittest.mock import Mock, MagicMock

from libvirttestapi.src import testcasexml, proxy
from libvirttestapi.src import exception as exc
from libvirttestapi.utils import utils
class TestInputVerify():
    def setup_method(self):
        base_path = utils.get_base_path()
        file_path = os.path.join(base_path, 'xmls', 'test', 'test.xml')
        self.filepath = file_path
        self.case_params = {
                'guestname': 'libvirt_test_api',
                'hddriver': 'virtio',
                }
        self.optional_params = {'imagesize': 1,
                   'imageformat': 'raw',
                   'qcow2version': 'basic',
                   'diskpath': '/var/lib/libvirt/images/attacheddisk',
                   'volumepath': '/var/lib/libvirt/images',
                   'volume': 'attacheddisk',
                   'dev': 'vdb',
                   'xml': 'xmls/test.xml',
                   }
        self.text = {'guestname': 'libvirt_test_api', 'hddriver': 'virtio', 'xml': '<disk device="disk" type="file">\n  <driver name="qemu" type="raw"/>\n  <source file="/var/lib/libvirt/images/attacheddisk"/>\n  <target bus="virtio" dev="vdb"/>\n  <readonly/>\n</disk>\n'}
        self.tostr = {'guestname': 'libvirt_test_api', 'hddriver': 'virtio', 'xml': '<disk device="disk" type="file">\n  <driver name="qemu" type="raw"/>\n  <source file="/var/lib/libvirt/images/attacheddisk"/>\n  <target bus="virtio" dev="vdb"/>\n  <readonly/>\n</disk>\n'}
    def test_populate_missing_filepath(self):
        self.filepath = 'noexist.xml'
        with pytest.raises(exc.FileDoesNotExist):
            testcasexml.populate_xml_file(self.filepath, self.case_params, self.optional_params)

    def test_populate_xmlfile_pass(self):
        result_str = testcasexml.populate_xml_file(self.filepath, self.case_params, self.optional_params)
        assert result_str == self.text

    def vtest_xmlfile_tostr_pass(self):
        proxy_object = Mock() 
        proxy_object.get_testcase_params = MagicMock(return_value=[self.case_params, self.optional_params])
        result_xml = testcasexml.xml_file_to_str(proxy_object, 'test:test', self.case_params)
        assert result_xml == self.tostr
