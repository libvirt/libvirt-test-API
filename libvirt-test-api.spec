# Disable the shebangs checks on scripts that currently dont'
# define a Python version
%global __brp_mangle_shebangs_exclude_from multicast_guest.py|netperf_agent.py|ksm_overcommit_guest.py|check_cpu_flag.py|virtio_console_guest.py|boottool.py|VirtIoChannel_guest_send_receive.py|serial_host_send_receive.py

%define with_python2 1
%if 0%{?fedora} > 30 || 0%{?rhel} > 7
%define with_python2 0
%endif

%define with_python3 0
%if 0%{?fedora} || 0%{?rhel} > 7
%define with_python3 1
%endif

Summary: Python based regression tests for libvirt API
Name: libvirt-test-api
Version: 0.0
Release: 1%{?dist}
License: GPLv2
URL: https://github.com/libvirt/libvirt-test-API
Source0: https://github.com/libvirt/libvirt-test-API/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz


%if %{with_python3}
BuildRequires: python3-devel, python3-setuptools, python3-six
Requires: python3-six, python3-lxml
%else
BuildRequires: python2-devel, python2-setuptools, python-six
Requires: python-six, python-lxml
%endif

%if 0%{?fedora} > 30
Requires:python3-libvirt
%endif

%if 0%{?rhel}
Requires:libvirt-python
%endif

BuildArch: noarch

%description
Libvirt-test-API is designed to test the functionality of libvirt
through Python bindings of libvirt API. It supports writing cases
by using the Python language. It supports testing for KVM and
Xen ethier paravirt (for which only Fedora and Red Hat Enterprise
Linux guests are currently supported) as well as fully virtualized guests.

%prep
%setup -q -n %{name}-%{version}

%build
%if %{with_python3}
%py3_build
%else
%py2_build
%endif

%install
%if %{with_python3}
%py3_install
%else
%py2_install
%endif

%if %{with_python2}
%files
%doc README.md
%license LICENSE
%{_bindir}/%{name}
%{python2_sitelib}/libvirt_test_api*
%{python2_sitelib}/libvirttestapi*
%{_datadir}/libvirt-test-api*
%endif

%if %{with_python3}
%files 
%doc README.md
%license LICENSE
%{_bindir}/%{name}
%{python3_sitelib}/libvirt_test_api*
%{python3_sitelib}/libvirttestapi*
%{_datadir}/libvirt-test-api*
%endif


%changelog
* Mon Dec 2 2019 Lily Nie <lnie@redhat.com> - 0.0-1
- New release

