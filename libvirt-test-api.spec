# Disable the shebangs checks on scripts that currently don't
# define a Python version..The point here is that these scripts
#will be copied to guest VM instances,which may be running
#Operating Systems that can haveeither Python 2 or Python 3,
#but it's impossible to know for sure at packaging time.
%global __brp_mangle_shebangs_exclude_from virtlab.py|jenkins.py

%global with_python2 1
%if 0%{?fedora} > 30 || 0%{?rhel} > 7
%global with_python2 0
%endif

%global with_python3 0
%if 0%{?fedora} > 30 || 0%{?rhel} > 7
%global with_python3 1
%endif

Summary: Python based regression tests for libvirt API
Name: libvirt-test-api
Version: 1.0
Release: 1%{?dist}
License: GPLv2
URL: https://gitlab.com/libvirt/libvirt-test-API
Source0: https://gitlab.com/libvirt/libvirt-test-API/-/archive/v1.0/%{name}-%{version}.tar.gz


%if %{with_python3}
BuildRequires: python3-devel
BuildRequires: python3-pytest
BuildRequires: python3-setuptools
BuildRequires: python3-six
BuildRequires: python3-attrs
BuildRequires: python3-pexpect
BuildRequires: mock

Requires: libvirt
Requires: qemu-kvm
Requires: qemu-img
Requires: python3-six
Requires: python3-lxml
Requires: python3-libvirt
Requires: virt-install


%else
BuildRequires: python2-devel
BuildRequires: python2-pytest
BuildRequires: python2-setuptools
BuildRequires: python2-attrs
BuildRequires: python-six
BuildRequires: python2-pexpect
BuildRequires: mock

Requires: libvirt
Requires: qemu-kvm
Requires: python-six
Requires: python-lxml
Requires: virt-install
%endif


%if 0%{?rhel} && 0%{?rhel} < 8
Requires:libvirt-python
%endif

BuildArch: noarch

%description
Libvirt-test-API is designed to test the functionality of libvirt
through Python bindings of libvirt API. It supports writing cases
by using the Python language. It supports testing for KVM and
Xen either paravirt (for which only Fedora and Red Hat Enterprise
Linux guests are currently supported) as well as fully virtualized guests.

%prep
%setup -q -n %{name}-%{version}

%check
%if %{with_python3}
%{__python3} setup.py test
%else
%{__python2} setup.py test
%endif

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
* Sat Apr 18 2020 Lily Nie <lnie@redhat.com> - 1.0-1
- New release

