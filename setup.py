# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
# Copyright: Red Hat Inc. 2013-2014

import os
import sys
import glob

# pylint: disable=E0611
from setuptools import setup, find_packages

def get_data_files():
    def add_files(level=[]):
        installed_location = ['usr', 'share', 'libvirt-test-api']
        installed_location += level
        level_str = '/'.join(level)
        if level_str:
            level_str += '/'
        file_glob = '%s*' % level_str
        files_found = [path for path in glob.glob(file_glob) if
                       os.path.isfile(path)]
        return [(os.path.join(*(['/'] + installed_location)), files_found)]
    data_files = add_files(["excute"])
    data_files_dirs = ['templates','cases','xmls','config']

    for data_file_dir in data_files_dirs:
        for root, dirs, files in os.walk(data_file_dir):
            if dirs:
                for subdir in dirs:
                    rt = root.split('/')
                    rt.append(subdir)
                    data_files += add_files(rt)
                if files:
                    data_files += add_files([root])
            else:
                data_files += add_files([root])


    return data_files


if __name__ == "__main__":

    setup(name='libvirt-test-api',
          version=2.0,
          description='Python based regression tests for libvirt API',
          author='Libvirt QE Team',
          author_email='lnie@redhat.com',
          url='https://github.com/libvirt/libvirt-test-API',
          license="GPLv2",
          packages=find_packages(exclude=('selftests*',)),
          package_data={'libvirttestapi': ["*.*"]},
          data_files=get_data_files(),
          include_package_data=True,
          entry_points={
              'console_scripts': ['libvirt-test-api=libvirttestapi.main:main'],
                
              },
          install_requires= ["pexpect"],
          )

