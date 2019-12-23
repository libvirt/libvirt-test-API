               Libvirt-test-API

    Python based regression tests for libvirt API


Libvirt-test-API is designed to test the functionality of libvirt
through Python bindings of libvirt API. It supports writing cases
by using the Python language. It supports testing for KVM and
Xen ethier paravirt (for which only Fedora and Red Hat Enterprise
Linux guests are currently supported) as well as fully virtualized
guests.


Documentation:

An user guide is available in publican/DocBook sources
under docs/User_Guide/libvirt-test-API_Guide it describes
the software goals, explain how to write new test software
and the configuration files for it, and then how to run the
tests. The last section explain how to hook it into Autotest.

A pregenerated PDF version is available at
  ftp://libvirt.org/libvirt/libvirt-test-API/Libvirt-test-API.pdf
or
  http://libvirt.org/sources/libvirt-test-API/Libvirt-test-API.pdf

To regenerate the documentation, you must have publican installed,
then cd to docs/User_Guide/libvirt-test-API_Guide, double check the
publican.cfg config file and then run make, the resulting files
will be generated in a tmp subdirectory.
