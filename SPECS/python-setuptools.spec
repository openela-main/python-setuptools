%global srcname setuptools

# The original RHEL 9 content set is defined by (build)dependencies
# of the packages in Fedora ELN. Hence we disable tests here
# to prevent pulling many unwanted packages in.
# Once the RHEL 9 content set is defined and/or RHEL 9 forks from ELN,
# the conditional can be removed from the Fedora spec file.
# We intentionally keep this enabled on EPEL.
%if 0%{?rhel} >= 9 && !0%{?epel}
%bcond_with tests
%else
%bcond_without tests
%endif

#  WARNING  When bootstrapping, disable tests as well,
#           because tests need pip.
%bcond_with bootstrap
# Similar to what we have in pythonX.Y.spec files.
# If enabled, provides unversioned executables and other stuff.
# Disable it if you build this package in an alternative stack.
%bcond_without main_python

%if %{without bootstrap}
%global python_wheel_name %{srcname}-%{version}-py3-none-any.whl
%global python3_record %{python3_sitelib}/%{srcname}-%{version}.dist-info/RECORD
%endif

Name:           python-setuptools
# When updating, update the bundled libraries versions bellow!
Version:        53.0.0
Release:        12%{?dist}
Summary:        Easily build and distribute Python packages
# setuptools is MIT
# appdirs is MIT
# ordered-set is MIT
# packaging is BSD or ASL 2.0
# pyparsing is MIT
# the setuptools logo has unknown license and possible TM problems,
# but the sdist **does not** contain it,
# see https://github.com/pypa/setuptools/issues/2227
License:        MIT and (BSD or ASL 2.0)
URL:            https://pypi.python.org/pypi/%{srcname}
Source0:        %{pypi_source %{srcname} %{version}}

# Two backports related to the License-File metadata field
# Fixes https://bugzilla.redhat.com/2033994
#
# license_files - Add support for glob patterns + add default patterns
# https://github.com/pypa/setuptools/pull/2620
# included in setuptools 56+
#
# Add License-File field to package metadata
# https://github.com/pypa/setuptools/pull/2645
# included in setuptools 57+
# depends on the previous one
Patch1:         license-file-metadata.patch

# Fix case sensitivity of entry point names and keys in setup.cfg
# Fixes https://bugzilla.redhat.com/2124281
Patch2:         https://github.com/pypa/setuptools/pull/2580.patch

# Security fix for CVE-2022-40897
# Regular Expression Denial of Service (ReDoS) in package_index.py
# Resolved upstream: https://github.com/pypa/setuptools/commit/43a9c9bfa6aa626ec2a22540bea28d2ca77964be
Patch3:         CVE-2022-40897.patch

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
%if %{with tests}
BuildRequires:  gcc
BuildRequires:  python%{python3_pkgversion}-pip
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-mock
BuildRequires:  python%{python3_pkgversion}-pytest-fixture-config
BuildRequires:  python%{python3_pkgversion}-pytest-virtualenv
BuildRequires:  python%{python3_pkgversion}-jaraco-envs
%endif # with tests
%if %{without bootstrap}
BuildRequires:  python%{python3_pkgversion}-pip
BuildRequires:  python%{python3_pkgversion}-wheel
BuildRequires:  python%{python3_pkgversion}-setuptools
# python3 bootstrap: this is built before the final build of python3, which
# adds the dependency on python3-rpm-generators, so we require it manually
# The minimal version is for bundled provides verification script
BuildRequires:  python3-rpm-generators >= 11-8
%endif # without bootstrap

%description
Setuptools is a collection of enhancements to the Python distutils that allow
you to more easily build and distribute Python packages, especially ones that
have dependencies on other packages.

This package also contains the runtime components of setuptools, necessary to
execute the software that requires pkg_resources.

# Virtual provides for the packages bundled by setuptools.
# Bundled packages are defined in two files:
# - pkg_resources/_vendor/vendored.txt, and
# - setuptools/_vendor/vendored.txt
# Merge them to one and then generate the list with:
# %%{_rpmconfigdir}/pythonbundles.py --namespace 'python%%{python3_pkgversion}dist' allvendor.txt
%global bundled %{expand:
Provides: bundled(python%{python3_pkgversion}dist(appdirs)) = 1.4.3
Provides: bundled(python%{python3_pkgversion}dist(ordered-set)) = 3.1.1
Provides: bundled(python%{python3_pkgversion}dist(packaging)) = 20.4
Provides: bundled(python%{python3_pkgversion}dist(pyparsing)) = 2.2.1
}

%package -n python%{python3_pkgversion}-setuptools
Summary:        Easily build and distribute Python 3 packages
%{bundled}

%if %{with bootstrap}
Provides:       python%{python3_pkgversion}dist(setuptools) = %{version}
Provides:       python%{python3_version}dist(setuptools) = %{version}
%endif

# For users who might see ModuleNotFoundError: No module named 'pkg_resoureces'
%py_provides    python%{python3_pkgversion}-pkg_resources
%py_provides    python%{python3_pkgversion}-pkg-resources

# Provide platform-python-setuptools for backwards compatibility with RHEL 8
Provides:       platform-python-setuptools = %{version}-%{release}

%description -n python%{python3_pkgversion}-setuptools
Setuptools is a collection of enhancements to the Python 3 distutils that allow
you to more easily build and distribute Python 3 packages, especially ones that
have dependencies on other packages.

This package also contains the runtime components of setuptools, necessary to
execute the software that requires pkg_resources.

%if %{without bootstrap}
%package -n     %{python_wheel_pkg_prefix}-%{srcname}-wheel
Summary:        The setuptools wheel
%{bundled}
Provides:       %{name}-wheel = %{version}-%{release}
Obsoletes:      %{name}-wheel < %{version}-%{release}

# Older versions of python3-libs expect Python wheels at the old unversioned
# location, so we conflict with the old Python versions that wouldn't work with
# the new wheel location.
Conflicts:      python3-libs < 3.9.9-2

%description -n %{python_wheel_pkg_prefix}-%{srcname}-wheel
A Python wheel of setuptools to use with venv.
%endif


%prep
%autosetup -p1 -n %{srcname}-%{version}
%if %{without bootstrap}
# If we don't have setuptools installed yet, we use the pre-generated .egg-info
# See https://github.com/pypa/setuptools/pull/2543
# And https://github.com/pypa/setuptools/issues/2550
rm -r %{srcname}.egg-info
%endif

# Strip shbang
find setuptools pkg_resources -name \*.py | xargs sed -i -e '1 {/^#!\//d}'
# Remove bundled exes
rm -f setuptools/*.exe
# These tests require internet connection
rm setuptools/tests/test_integration.py 
# We don't do linting or coverage here
sed -i pytest.ini -e 's/ --flake8//' \
                  -e 's/ --cov//'

%build
%if %{without bootstrap}
%py3_build_wheel
%else
%py3_build
%endif


%install
%if %{without bootstrap}
%py3_install_wheel %{python_wheel_name}
%else
%py3_install
%endif

# This is not installed (in 45.2.0 anyway), but better be safe than sorry
rm -rf %{buildroot}%{python3_sitelib}/{setuptools,pkg_resources}/tests

%if %{without bootstrap}
sed -i '/^setuptools\/tests\//d' %{buildroot}%{python3_record}
%endif

find %{buildroot}%{python3_sitelib} -name '*.exe' | xargs rm -f

# Don't ship these
rm -r docs/{conf.py,_*}

%if %{without bootstrap}
mkdir -p %{buildroot}%{python_wheel_dir}
install -p dist/%{python_wheel_name} -t %{buildroot}%{python_wheel_dir}
%endif

%if %{with tests}
%check
# Verify bundled provides are up to date
cat pkg_resources/_vendor/vendored.txt setuptools/_vendor/vendored.txt > allvendor.txt
%{_rpmconfigdir}/pythonbundles.py allvendor.txt --namespace 'python%{python3_pkgversion}dist' --compare-with '%{bundled}'

# Regression test, the wheel should not be larger than 600 KiB
# https://bugzilla.redhat.com/show_bug.cgi?id=1914481#c3
test $(du dist/%{python_wheel_name} | cut -f1) -lt 600

# Upstream tests
# --ignore=pavement.py:
#   pavement.py is only used by upstream to do releases and vendoring, we don't ship it
PYTHONPATH=$(pwd) %pytest --ignore=pavement.py
%endif # with tests


%files -n python%{python3_pkgversion}-setuptools
%license LICENSE
%doc docs/* CHANGES.rst README.rst
%{python3_sitelib}/pkg_resources/
%{python3_sitelib}/setuptools*/
%{python3_sitelib}/_distutils_hack/
%{python3_sitelib}/distutils-precedence.pth

%if %{without bootstrap}
%files -n %{python_wheel_pkg_prefix}-%{srcname}-wheel
%license LICENSE
# we own the dir for simplicity
%dir %{python_wheel_dir}/
%{python_wheel_dir}/%{python_wheel_name}
%endif


%changelog
* Wed Jan 11 2023 Charalampos Stratakis <cstratak@redhat.com> - 53.0.0-12
- Security fix for CVE-2022-40897
Resolves: rhbz#2158559

* Wed Sep 07 2022 Miro Hrončok <mhroncok@redhat.com> - 53.0.0-11
- Fix case sensitivity of entry point names and keys in setup.cfg
- Resolves: rhbz#2124281

* Tue Feb 08 2022 Tomas Orsava <torsava@redhat.com> - 53.0.0-10
- Add automatically generated Obsoletes tag with the python39- prefix
  for smoother upgrade from RHEL8
- Related: rhbz#1990421

* Wed Jan 12 2022 Miro Hrončok <mhroncok@redhat.com> - 53.0.0-9
- Add License-File field to package metadata
- Resolves: rhbz#2033994

* Wed Nov 24 2021 Tomas Orsava <torsava@redhat.com> - 53.0.0-8
- Conflict with old Python versions that use the old unversioned wheel location
- Resolves: rhbz#1982668

* Wed Sep 22 2021 Tomas Orsava <torsava@redhat.com> - 53.0.0-7
- Make the python-setuptools-wheel subpackage versioned (python3-setuptools-wheel),
  and move its contents to a versioned directory /usr/share/python3-wheels
- Resolves: rhbz#1982668

* Tue Aug 10 2021 Mohan Boddu <mboddu@redhat.com>
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Wed Jul 28 2021 Tomas Orsava <torsava@redhat.com> - 53.0.0-5
- Provide the platform-python-setuptools name for backwards compatibility
  with RHEL 8
- Related: rhbz#1891487

* Mon Jun 21 2021 Lumír Balhar <lbalhar@redhat.com> - 53.0.0-4
- Add missing bundled provide - ordered-set
Related: rhbz#1950291

* Thu Apr 22 2021 Miro Hrončok <mhroncok@redhat.com> - 53.0.0-3
- Provide python3-pkg_resources
- Provide python3-pkg-resources
Resolves: rhbz#1947857

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 53.0.0-2
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Tue Feb 02 2021 Miro Hrončok <mhroncok@redhat.com> - 53.0.0-1
- Update to 53.0.0
- https://setuptools.readthedocs.io/en/latest/history.html#v53-0-0
- Fixes: rhbz#1923249

* Tue Jan 26 2021 Lumír Balhar <lbalhar@redhat.com> - 52.0.0-1
- Update to 52.0.0 (#1917060)
- Removes easy_install module and executable

* Mon Jan 11 2021 Miro Hrončok <mhroncok@redhat.com> - 51.1.2-1
- Update to 51.1.2
- Removes tests from the wheel
- https://setuptools.readthedocs.io/en/latest/history.html#v51-1-2
- Fixes: rhbz#1914481

* Tue Dec 29 2020 Miro Hrončok <mhroncok@redhat.com> - 51.1.1-1
- Update to 51.1.1
- Fixes test failures with pip 20.3 as well as with pytest 6.2+
- Fixes: rhbz#1909575

* Fri Dec  4 2020 Miro Hrončok <mhroncok@redhat.com> - 50.3.2-2
- Disable tests in Fedora ELN (and RHEL)

* Tue Oct 20 2020 Tomas Hrnciar <thrnciar@redhat.com> - 50.3.2-1
- Update to 50.3.2 (#1889093)

* Fri Sep 04 2020 Tomas Hrnciar <thrnciar@redhat.com> - 50.1.0-1
- Update to 50.1.0 (#1873889)

* Fri Aug 21 2020 Petr Viktorin <pviktori@redhat.com> - 49.6.0-1
- Update to 49.6.0 (#1862791)

* Wed Jul 29 2020 Miro Hrončok <mhroncok@redhat.com> - 49.1.3-1
- Update to 49.1.3 (#1853597)
- https://setuptools.readthedocs.io/en/latest/history.html#v49-1-3

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 47.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jun 26 2020 Miro Hrončok <mhroncok@redhat.com> - 47.3.1-1
- Update to 47.3.1 (#1847049)
- https://setuptools.readthedocs.io/en/latest/history.html#v47-3-1

* Mon Jun 01 2020 Charalampos Stratakis <cstratak@redhat.com> - 47.1.1-1
- Update to 47.1.1 (#1841123)
- https://setuptools.readthedocs.io/en/latest/history.html#v47-1-1

* Sun May 24 2020 Miro Hrončok <mhroncok@redhat.com> - 46.4.0-4
- Rebuilt for Python 3.9

* Thu May 21 2020 Miro Hrončok <mhroncok@redhat.com> - 46.4.0-3
- Bootstrap for Python 3.9

* Thu May 21 2020 Miro Hrončok <mhroncok@redhat.com> - 46.4.0-2
- Bootstrap for Python 3.9

* Mon May 18 2020 Tomas Hrnciar <thrnciar@redhat.com> - 46.4.0-1
- Update to 46.4.0 (#1835411)
- https://setuptools.readthedocs.io/en/latest/history.html#v46-4-0

* Tue May 12 2020 Tomas Hrnciar <thrnciar@redhat.com> - 46.2.0-1
- Update to 46.2.0 (#1833826)
- https://setuptools.readthedocs.io/en/latest/history.html#v46-2-0

* Thu Mar 26 2020 Miro Hrončok <mhroncok@redhat.com> - 46.1.3-1
- Upgrade to 46.1.3 (#1817189)
- https://setuptools.readthedocs.io/en/latest/history.html#v46-1-3

* Tue Mar 10 2020 Miro Hrončok <mhroncok@redhat.com> - 46.0.0-1
- Upgrade to 46.0.0 (#1811340)
- https://setuptools.readthedocs.io/en/latest/history.html#v46-0-0

* Tue Feb 11 2020 Miro Hrončok <mhroncok@redhat.com> - 45.2.0-1
- Upgrade to 45.2.0 (#1775943)
- https://setuptools.readthedocs.io/en/latest/history.html#v45-2-0
- No longer supports Python 2

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 41.6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Nov 04 2019 Tomas Orsava <torsava@redhat.com> - 41.6.0-1
- Upgrade to 41.6.0 (#1758945).
- https://setuptools.readthedocs.io/en/latest/history.html#v41-6-0
- Disabled a failing upstream test: https://github.com/pypa/setuptools/issues/1896

* Tue Sep 03 2019 Randy Barlow <bowlofeggs@fedoraproject.org> - 41.2.0-1
- Upgrade to 41.2.0 (#1742718).
- https://setuptools.readthedocs.io/en/latest/history.html#v41-2-0

* Mon Aug 26 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-9
- Move python2-setuptools to a separate package

* Sun Aug 18 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-8
- Rebuilt for Python 3.8

* Wed Aug 14 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-7
- Bootstrap for Python 3.8

* Wed Aug 14 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-6
- Provide pythonXdist(setuptools) when bootstrapping

* Wed Aug 14 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-5
- Bootstrap for Python 3.8

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 41.0.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Tue Jul 16 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-3
- Make /usr/bin/easy_install Python 3
- Drop obsoleted Obsoletes

* Fri Jun 21 2019 Petr Viktorin <pviktori@redhat.com> - 41.0.1-2
- Remove optional test dependencies for Python 2
- Skip test_virtualenv on Python 2

* Thu Apr 25 2019 Miro Hrončok <mhroncok@redhat.com> - 41.0.1-1
- Update to 41.0.1 (#1695846)
- https://github.com/pypa/setuptools/blob/v41.0.1/CHANGES.rst

* Tue Feb 05 2019 Miro Hrončok <mhroncok@redhat.com> - 40.8.0-1
- Update to 40.8.0 (#1672756)
- https://github.com/pypa/setuptools/blob/v40.8.0/CHANGES.rst

* Sun Feb 03 2019 Miro Hrončok <mhroncok@redhat.com> - 40.7.3-1
- Hotfix update to 40.7.3 (#1672084)
- https://github.com/pypa/setuptools/blob/v40.7.3/CHANGES.rst

* Sat Feb 02 2019 Miro Hrončok <mhroncok@redhat.com> - 40.7.2-1
- Hotfix update to 40.7.2 (#1671608)
- https://github.com/pypa/setuptools/blob/v40.7.2/CHANGES.rst

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 40.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Jan 29 2019 Miro Hrončok <mhroncok@redhat.com> - 40.7.1-1
- Hotfix update to 40.7.1 (#1670243)
- https://github.com/pypa/setuptools/blob/v40.7.1/CHANGES.rst

* Mon Jan 28 2019 Miro Hrončok <mhroncok@redhat.com> - 40.7.0-1
- Update to 40.7.0 (#1669876)
- https://github.com/pypa/setuptools/blob/v40.7.0/CHANGES.rst

* Mon Sep 24 2018 Miro Hrončok <mhroncok@redhat.com> - 40.4.3-1
- Update to 40.4.3 to fix dire DeprecationWarnings (#1627071)
- List vendored libraries
- https://github.com/pypa/setuptools/blob/v40.4.3/CHANGES.rst

* Wed Sep 19 2018 Randy Barlow <bowlofeggs@fedoraproject.org> - 40.4.1-1
- Update to 40.4.1 (#1599307).
- https://github.com/pypa/setuptools/blob/v40.4.1/CHANGES.rst

* Wed Aug 15 2018 Petr Viktorin <pviktori@redhat.com> - 39.2.0-7
- Add a subpackage with wheels
- Remove the python3 bcond
- Remove macros for RHEL 6

* Thu Jul 19 2018 Miro Hrončok <mhroncok@redhat.com> - 39.2.0-6
- Create /usr/local/lib/pythonX.Y when needed (#1576924)

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 39.2.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Mon Jun 18 2018 Miro Hrončok <mhroncok@redhat.com> - 39.2.0-4
- Rebuilt for Python 3.7

* Wed Jun 13 2018 Miro Hrončok <mhroncok@redhat.com> - 39.2.0-3
- Bootstrap for Python 3.7

* Wed Jun 13 2018 Miro Hrončok <mhroncok@redhat.com> - 39.2.0-2
- Bootstrap for Python 3.7

* Wed May 23 2018 Charalampos Stratakis <cstratak@redhat.com> - 39.2.0-1
- update to 39.2.0 Fixes bug #1572889

* Tue Mar 20 2018 Charalampos Stratakis <cstratak@redhat.com> - 39.0.1-1
- update to 39.0.1 Fixes bug #1531527

* Wed Mar 14 2018 Tomas Orsava <torsava@redhat.com> - 38.4.0-4
- Skip test_virtualenv due to broken executable detection

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 38.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 16 2018 Troy Dawson <tdawson@redhat.com> - 38.4.0-2
- Update conditional

* Tue Jan 16 2018 Charalampos Stratakis <cstratak@redhat.com> - 38.4.0-1
- update to 38.4.0 Fixes bug #1531527

* Tue Jan 02 2018 Charalampos Stratakis <cstratak@redhat.com> - 38.2.5-1
- update to 38.2.5 Fixes bug #1528968

* Tue Nov 21 2017 Miro Hrončok <mhroncok@redhat.com> - 37.0.0-1
- Update to 37.0.0 (fixes #1474126)
- Removed not needed pip3 patch (upstream included different version of fix)

* Tue Nov 21 2017 Miro Hrončok <mhroncok@redhat.com> - 36.5.0-1
- Update to 36.5.0 (related to #1474126)

* Thu Nov 09 2017 Tomas Orsava <torsava@redhat.com> - 36.2.0-8
- Remove the platform-python subpackage

* Sun Aug 20 2017 Tomas Orsava <torsava@redhat.com> - 36.2.0-7
- Re-enable tests to finish bootstrapping the platform-python stack
  (https://fedoraproject.org/wiki/Changes/Platform_Python_Stack)

* Wed Aug 09 2017 Tomas Orsava <torsava@redhat.com> - 36.2.0-6
- Add the platform-python subpackage
- Disable tests so platform-python stack can be bootstrapped
  (https://fedoraproject.org/wiki/Changes/Platform_Python_Stack)

* Wed Aug 09 2017 Tomas Orsava <torsava@redhat.com> - 36.2.0-5
- Add Patch 0 that fixes a test suite failure on Python 3 in absence of
  the Python 2 version of pip
- Move docs to their proper place

* Wed Aug 09 2017 Tomas Orsava <torsava@redhat.com> - 36.2.0-4
- Switch macros to bcond's and make Python 2 optional to facilitate building
  the Python 2 and Python 3 modules.

* Tue Aug 08 2017 Michal Cyprian <mcyprian@redhat.com> - 36.2.0-3
- Revert "Add --executable option to easy_install command"
  This enhancement is currently not needed and it can possibly
  collide with `pip --editable`option

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 36.2.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Jul 15 2017 Charalampos Stratakis <cstratak@redhat.com> - 36.2.0-1
- update to 36.2.0. Fixes bug #1470908

* Thu Jun 15 2017 Charalampos Stratakis <cstratak@redhat.com> - 36.0.1-1
- update to 36.0.1. Fixes bug #1458093

* Sat May 27 2017 Kevin Fenzi <kevin@scrye.com> - 35.0.2-1
- update to 35.0.2. Fixes bug #1446622

* Sun Apr 23 2017 Kevin Fenzi <kevin@scrye.com> - 35.0.1-1
- Update to 35.0.1. Fixes bug #1440388

* Sat Mar 25 2017 Kevin Fenzi <kevin@scrye.com> - 34.3.2-1
- Update to 34.3.2. Fixes bug #1428818

* Sat Feb 25 2017 Kevin Fenzi <kevin@scrye.com> - 34.3.0-1
- Update to 34.3.0. Fixes bug #1426463

* Fri Feb 17 2017 Michal Cyprian <mcyprian@redhat.com> - 34.2.0-2
- Add --executable option to easy_install command

* Thu Feb 16 2017 Charalampos Stratakis <cstratak@redhat.com> - 34.2.0-1
- Update to 34.2.0. Fixes bug #1421676

* Sat Feb 04 2017 Kevin Fenzi <kevin@scrye.com> - 34.1.1-1
- Update to 34.1.1. Fixes bug #1412268
- Fix License tag. Fixes bug #1412268
- Add Requires for fomerly bundled projects: six, packaging appdirs

* Tue Jan 03 2017 Michal Cyprian <mcyprian@redhat.com> - 32.3.1-2
- Use python macros in build and install sections

* Thu Dec 29 2016 Kevin Fenzi <kevin@scrye.com> - 32.3.1-1
- Update to 32.3.1. Fixes bug #1409091

* Wed Dec 28 2016 Kevin Fenzi <kevin@scrye.com> - 32.3.0-1
- Update to 32.3.0. Fixes bug #1408564

* Fri Dec 23 2016 Kevin Fenzi <kevin@scrye.com> - 32.2.0-1
- Update to 32.2.0. Fixes bug #1400310

* Tue Dec 13 2016 Stratakis Charalampos <cstratak@redhat.com> - 30.4.0-2
- Enable tests

* Sun Dec 11 2016 Kevin Fenzi <kevin@scrye.com> - 30.4.0-1
- Update to 30.4.0. Fixes bug #1400310

* Fri Dec 09 2016 Charalampos Stratakis <cstratak@redhat.com> - 28.8.0-3
- Rebuild for Python 3.6 with wheel
- Disable tests

* Fri Dec 09 2016 Charalampos Stratakis <cstratak@redhat.com> - 28.8.0-2
- Rebuild for Python 3.6 without wheel

* Wed Nov 09 2016 Kevin Fenzi <kevin@scrye.com> - 28.8.0-1
- Update to 28.8.1. Fixes bug #1392722

* Mon Oct 31 2016 Kevin Fenzi <kevin@scrye.com> - 28.7.1-1
- Update to 28.7.1. Fixes bug #1389917

* Tue Oct 25 2016 Kevin Fenzi <kevin@scrye.com> - 28.6.1-1
- Update to 28.6.1. Fixes bug #1387071

* Tue Oct 18 2016 Kevin Fenzi <kevin@scrye.com> - 28.6.0-1
- Update to 28.6.0. Fixes bug #1385655

* Sat Oct 08 2016 Kevin Fenzi <kevin@scrye.com> - 28.3.0-1
- Update to 28.3.0. Fixes bug #1382971

* Sun Oct 02 2016 Kevin Fenzi <kevin@scrye.com> - 28.2.0-1
- Update to 28.2.0. Fixes bug #1381099

* Sun Oct 02 2016 Kevin Fenzi <kevin@scrye.com> - 28.1.0-1
- Update to 28.1.0. Fixes bug #1381066

* Wed Sep 28 2016 Kevin Fenzi <kevin@scrye.com> - 28.0.0-1
- Update to 28.0.0. Fixes bug #1380073

* Sun Sep 25 2016 Kevin Fenzi <kevin@scrye.com> - 27.3.0-1
- Update to 27.3.0. Fixes bug #1378067

* Sat Sep 17 2016 Kevin Fenzi <kevin@scrye.com> - 27.2.0-1
- Update to 27.2.0. Fixes bug #1376298

* Sat Sep 10 2016 Kevin Fenzi <kevin@scrye.com> - 27.1.2-1
- Update to 27.1.2. Fixes bug #1370777

* Sat Aug 27 2016 Kevin Fenzi <kevin@scrye.com> - 26.0.0-1
- Update to 26.0.0. Fixes bug #1370777

* Wed Aug 10 2016 Kevin Fenzi <kevin@scrye.com> - 25.1.6-1
- Update to 25.1.6. Fixes bug #1362325

* Fri Jul 29 2016 Kevin Fenzi <kevin@scrye.com> - 25.1.1-1
- Update to 25.1.1. Fixes bug #1361465

* Thu Jul 28 2016 Kevin Fenzi <kevin@scrye.com> - 25.1.0-1
- Update to 25.1.0

* Sat Jul 23 2016 Kevin Fenzi <kevin@scrye.com> - 25.0.0-1
- Update to 25.0.0

* Fri Jul 22 2016 Kevin Fenzi <kevin@scrye.com> - 24.2.0-1
- Update to 24.2.0. Fixes bug #1352734

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 24.0.1-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Mon Jul 04 2016 Kevin Fenzi <kevin@scrye.com> - 24.0.1-1
- Update to 24.0.1. Fixes bug #1352532

* Wed Jun 15 2016 Kevin Fenzi <kevin@scrye.com> - 23.0.0-1
- Update to 23.0.0. Fixes bug #1346542

* Tue Jun 07 2016 Kevin Fenzi <kevin@scrye.com> - 22.0.5-1
- Update to 22.0.5. Fixes bug #1342706

* Thu Jun 02 2016 Kevin Fenzi <kevin@scrye.com> - 20.0.0-1
- Upgrade to 22.0.0

* Tue May 31 2016 Nils Philippsen <nils@redhat.com>
- fix source URL

* Sun May 29 2016 Kevin Fenzi <kevin@scrye.com> - 21.2.2-1
- Update to 21.2.2. Fixes bug #1332357

* Thu Apr 28 2016 Kevin Fenzi <kevin@scrye.com> - 20.10.1-1
- Update to 20.10.1. Fixes bug #1330375

* Sat Apr 16 2016 Kevin Fenzi <kevin@scrye.com> - 20.9.0-1
- Update to 20.9.0. Fixes bug #1327827

* Fri Apr 15 2016 Kevin Fenzi <kevin@scrye.com> - 20.8.1-1
- Update to 20.8.1. Fixes bug #1325910

* Thu Mar 31 2016 Kevin Fenzi <kevin@scrye.com> - 20.6.7-1
- Update to 20.6.7. Fixes bug #1322836

* Wed Mar 30 2016 Kevin Fenzi <kevin@scrye.com> - 20.4-1
- Update to 20.4. Fixes bug #1319366

* Wed Mar 16 2016 Kevin Fenzi <kevin@scrye.com> - 20.3-1
- Update to 20.3. Fixes bug #1311967

* Sat Feb 27 2016 Kevin Fenzi <kevin@scrye.com> - 20.2.2-1
- Update to 20.2.2. Fixes bug #1311967

* Sat Feb 13 2016 Kevin Fenzi <kevin@scrye.com> - 20.1.1-1
- Update to 20.1.1. Fixes bug #130719

* Fri Feb 12 2016 Kevin Fenzi <kevin@scrye.com> - 20.1-1
- Update to 20.1. Fixes bug #1307000

* Mon Feb 08 2016 Kevin Fenzi <kevin@scrye.com> - 20.0-1
- Update to 20.0. Fixes bug #1305394

* Sat Feb 06 2016 Kevin Fenzi <kevin@scrye.com> - 19.7-1
- Update to 19.7. Fixes bug #1304563

* Wed Feb 3 2016 Orion Poplawski <orion@cora.nwra.com> - 19.6.2-2
- Fix python3 package file ownership

* Sun Jan 31 2016 Kevin Fenzi <kevin@scrye.com> - 19.6.2-1
- Update to 19.6.2. Fixes bug #1303397

* Mon Jan 25 2016 Kevin Fenzi <kevin@scrye.com> - 19.6-1
- Update to 19.6.

* Mon Jan 25 2016 Kevin Fenzi <kevin@scrye.com> - 19.5-1
- Update to 19.5. Fixes bug #1301313

* Mon Jan 18 2016 Kevin Fenzi <kevin@scrye.com> - 19.4-1
- Update to 19.4. Fixes bug #1299288

* Tue Jan 12 2016 Orion Poplawski <orion@cora.nwra.com> - 19.2-2
- Cleanup spec from python3-setuptools review

* Fri Jan 08 2016 Kevin Fenzi <kevin@scrye.com> - 19.2-1
- Update to 19.2. Fixes bug #1296755

* Fri Dec 18 2015 Kevin Fenzi <kevin@scrye.com> - 19.1.1-1
- Update to 19.1.1. Fixes bug #1292658

* Tue Dec 15 2015 Kevin Fenzi <kevin@scrye.com> - 18.8.1-1
- Update to 18.8.1. Fixes bug #1291678

* Sat Dec 12 2015 Kevin Fenzi <kevin@scrye.com> - 18.8-1
- Update to 18.8. Fixes bug #1290942

* Fri Dec 04 2015 Kevin Fenzi <kevin@scrye.com> - 18.7.1-1
- Update to 18.7.1. Fixes bug #1287372

* Wed Nov 25 2015 Kevin Fenzi <kevin@scrye.com> - 18.6.1-1
- Update to 18.6.1. Fixes bug #1270578

* Sun Nov 15 2015 Thomas Spura <tomspur@fedoraproject.org> - 18.5-3
- Try to disable zip_safe bug #1271776
- Add python2 subpackage

* Fri Nov 06 2015 Robert Kuska <rkuska@redhat.com> - 18.5-2
- Add patch so it is possible to set test_args variable

* Tue Nov 03 2015 Robert Kuska <rkuska@redhat.com> - 18.5-1
- Update to 18.5. Fixes bug #1270578

* Tue Oct 13 2015 Robert Kuska <rkuska@redhat.coM> - 18.4-1
- Update to 18.4. Fixes bug #1270578
- Build with wheel and check phase

* Wed Sep 23 2015 Robert Kuska <rkuska@redhat.com> - 18.3.2-2
- Python3.5 rebuild: rebuild without wheel and check phase

* Tue Sep 22 2015 Kevin Fenzi <kevin@scrye.com> 18.3.2-1
- Update to 18.3.2. Fixes bug #1264902

* Mon Sep 07 2015 Kevin Fenzi <kevin@scrye.com> 18.3.1-1
- Update to 18.3.1. Fixes bug #1256188

* Wed Aug 05 2015 Kevin Fenzi <kevin@scrye.com> 18.1-1
- Update to 18.1. Fixes bug #1249436

* Mon Jun 29 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 18.0.1-2
- Explicitely provide python2-setuptools

* Thu Jun 25 2015 Kevin Fenzi <kevin@scrye.com> 18.0.1-1
- Update to 18.0.1

* Sat Jun 20 2015 Kevin Fenzi <kevin@scrye.com> 17.1.1-3
- Drop no longer needed Requires/BuildRequires on python-backports-ssl_match_hostname
- Fixes bug #1231325

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 17.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Jun 10 2015 Kevin Fenzi <kevin@scrye.com> 17.1.1-1
- Update to 17.1.1. Fixes bug 1229507

* Sun Jun 07 2015 Kevin Fenzi <kevin@scrye.com> 17.1-1
- Update to 17.1. Fixes bug 1229066

* Sat May 30 2015 Kevin Fenzi <kevin@scrye.com> 17.0-1
- Update to 17

* Mon May 18 2015 Kevin Fenzi <kevin@scrye.com> 16.0-1
- Update to 16

* Mon Apr 27 2015 Ralph Bean <rbean@redhat.com> - 15.2-1
- new version

* Sat Apr 04 2015 Ralph Bean <rbean@redhat.com> - 15.0-1
- new version

* Sun Mar 22 2015 Ralph Bean <rbean@redhat.com> - 14.3.1-1
- new version

* Sat Mar 21 2015 Ralph Bean <rbean@redhat.com> - 14.3.1-1
- new version

* Mon Mar 16 2015 Ralph Bean <rbean@redhat.com> - 14.3-1
- new version

* Sun Mar 15 2015 Ralph Bean <rbean@redhat.com> - 14.2-1
- new version

* Sun Mar 15 2015 Ralph Bean <rbean@redhat.com> - 14.1.1-1
- new version

* Fri Mar 06 2015 Ralph Bean <rbean@redhat.com> - 13.0.2-1
- new version

* Thu Mar 05 2015 Ralph Bean <rbean@redhat.com> - 12.4-1
- new version

* Fri Feb 27 2015 Ralph Bean <rbean@redhat.com> - 12.3-1
- new version

* Tue Jan 20 2015 Kevin Fenzi <kevin@scrye.com> 12.0.3-1
- Update to 12.0.3

* Fri Jan 09 2015 Slavek Kabrda <bkabrda@redhat.com> - 11.3.1-2
- Huge spec cleanup
- Make spec buildable on all Fedoras and RHEL 6 and 7
- Make tests actually run

* Wed Jan 07 2015 Kevin Fenzi <kevin@scrye.com> 11.3.1-1
- Update to 11.3.1. Fixes bugs: #1179393 and #1178817

* Sun Jan 04 2015 Kevin Fenzi <kevin@scrye.com> 11.0-1
- Update to 11.0. Fixes bug #1178421

* Fri Dec 26 2014 Kevin Fenzi <kevin@scrye.com> 8.2.1-1
- Update to 8.2.1. Fixes bug #1175229

* Thu Oct 23 2014 Ralph Bean <rbean@redhat.com> - 7.0-1
- Latest upstream.  Fixes bug #1154590.

* Mon Oct 13 2014 Ralph Bean <rbean@redhat.com> - 6.1-1
- Latest upstream.  Fixes bug #1152130.

* Sat Oct 11 2014 Ralph Bean <rbean@redhat.com> - 6.0.2-2
- Modernized python2 macros.
- Inlined locale environment variables in the %%check section.
- Remove bundled egg-info and .exes.

* Fri Oct 03 2014 Kevin Fenzi <kevin@scrye.com> 6.0.2-1
- Update to 6.0.2

* Sat Sep 27 2014 Kevin Fenzi <kevin@scrye.com> 6.0.1-1
- Update to 6.0.1. Fixes bug #1044444

* Mon Jun 30 2014 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-8
- Remove the python-setuptools-devel Virtual Provides as per this Fedora 21
  Change: http://fedoraproject.org/wiki/Changes/Remove_Python-setuptools-devel

* Mon Jun 30 2014 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-7
- And another bug in sdist

* Mon Jun 30 2014 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-6
- Fix a bug in the sdist command

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Apr 25 2014 Matej Stuchlik <mstuchli@redhat.com> - 2.0-4
- Rebuild as wheel for Python 3.4

* Thu Apr 24 2014 Tomas Radej <tradej@redhat.com> - 2.0-3
- Rebuilt for tag f21-python

* Wed Apr 23 2014 Matej Stuchlik <mstuchli@redhat.com> - 2.0-2
- Add a switch to build setuptools as wheel

* Mon Dec  9 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 2.0-1
- Update to new upstream release with a few things removed from the API:
  Changelog: https://pypi.python.org/pypi/setuptools#id139

* Mon Nov 18 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.4-1
- Update to 1.4 that gives easy_install pypi credential handling

* Thu Nov  7 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.3.1-1
- Minor upstream update to reign in overzealous warnings

* Mon Nov  4 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.3-1
- Upstream update that pulls in our security patches

* Mon Oct 28 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.1.7-1
- Update to newer upstream release that has our patch to the unittests
- Fix for http://bugs.python.org/issue17997#msg194950 which affects us since
  setuptools copies that code. Changed to use
  python-backports-ssl_match_hostname so that future issues can be fixed in
  that package.

* Sat Oct 26 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.1.6-1
- Update to newer upstream release.  Some minor incompatibilities listed but
  they should affect few, if any consumers.

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 23 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.9.6-1
- Upstream update -- just fixes python-2.4 compat

* Tue Jul 16 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.9.5-1
- Update to 0.9.5
  - package_index can handle hashes other than md5
  - Fix security vulnerability in SSL certificate validation
  - https://bugzilla.redhat.com/show_bug.cgi?id=963260

* Fri Jul  5 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.8-1
- Update to upstream 0.8  release.  Codebase now runs on anything from
  python-2.4 to python-3.3 without having to be translated by 2to3.

* Wed Jul  3 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.7.7-1
- Update to 0.7.7 upstream release

* Mon Jun 10 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.7.2-2
- Update to the setuptools-0.7 branch that merges distribute and setuptools

* Thu Apr 11 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.36-1
- Update to upstream 0.6.36.  Many bugfixes

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.28-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Aug 03 2012 David Malcolm <dmalcolm@redhat.com> - 0.6.28-3
- rebuild for https://fedoraproject.org/wiki/Features/Python_3.3

* Fri Aug  3 2012 David Malcolm <dmalcolm@redhat.com> - 0.6.28-2
- remove rhel logic from with_python3 conditional

* Mon Jul 23 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.28-1
- New upstream release:
  - python-3.3 fixes
  - honor umask when setuptools is used to install other modules

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.27-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jun 11 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.27-2
- Fix easy_install.py having a python3 shebang in the python2 package

* Thu Jun  7 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.27-1
- Upstream bugfix

* Tue May 15 2012 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.24-2
- Upstream bugfix

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.24-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Oct 17 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.24-1
- Upstream bugfix
- Compile the win32 launcher binary using mingw

* Sun Aug 21 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.21-1
- Upstream bugfix release

* Thu Jul 14 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.19-1
- Upstream bugfix release

* Tue Feb 22 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.14-7
- Switch to patch that I got in to upstream

* Tue Feb 22 2011 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.14-6
- Fix build on python-3.2

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.14-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sun Aug 22 2010 Thomas Spura <tomspur@fedoraproject.org> - 0.6.14-4
- rebuild with python3.2
  http://lists.fedoraproject.org/pipermail/devel/2010-August/141368.html

* Tue Aug 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.14-3
- Update description to mention this is distribute

* Thu Jul 22 2010 Thomas Spura <tomspur@fedoraproject.org> - 0.6.14-2
- bump for building against python 2.7

* Thu Jul 22 2010 Thomas Spura <tomspur@fedoraproject.org> - 0.6.14-1
- update to new version
- all patches are upsteam

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 0.6.13-7
- generalize path of easy_install-2.6 and -3.1 to -2.* and -3.*

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 0.6.13-6
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Sat Jul 3 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-5
- Upstream patch for compatibility problem with setuptools
- Minor spec cleanups
- Provide python-distribute for those who see an import distribute and need
  to get the proper package.

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-4
- Fix race condition in unittests under the python-2.6.x on F-14.

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-3
- Fix few more buildroot macros

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-2
- Include data that's needed for running tests

* Thu Jun 10 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.13-1
- Update to upstream 0.6.13
- Minor specfile formatting fixes

* Thu Feb 04 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.10-3
- First build with python3 support enabled.
  
* Fri Jan 29 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.10-2
- Really disable the python3 portion

* Fri Jan 29 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.10-1
- Update the python3 portions but disable for now.
- Update to 0.6.10
- Remove %%pre scriptlet as the file has a different name than the old
  package's directory

* Tue Jan 26 2010 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.9-4
- Fix install to make /usr/bin/easy_install the py2 version
- Don't need python3-tools since the library is now in the python3 package
- Few other changes to cleanup style

* Fri Jan 22 2010 David Malcolm <dmalcolm@redhat.com> - 0.6.9-2
- add python3 subpackage

* Mon Dec 14 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.9-1
- New upstream bugfix release.

* Sun Dec 13 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.8-2
- Test rebuild

* Mon Nov 16 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.8-1
- Update to 0.6.8.
- Fix directory => file transition when updating from setuptools-0.6c9.

* Tue Nov 3 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.7-2
- Fix duplicate inclusion of files.
- Only Obsolete old versions of python-setuptools-devel

* Tue Nov 3 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.7-1
- Move easy_install back into the main package as the needed files have been
  moved from python-devel to the main python package.
- Update to 0.6.7 bugfix.

* Fri Oct 16 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.6-1
- Upstream bugfix release.

* Mon Oct 12 2009 Toshio Kuratomi <toshio@fedoraproject.org> - 0.6.4-1
- First build from the distribute codebase -- distribute-0.6.4.
- Remove svn patch as upstream has chosen to go with an easier change for now.

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6c9-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Jul 14 2009 Konstantin Ryabitsev <icon@fedoraproject.org> - 0.6c9-4
- Apply SVN-1.6 versioning patch (rhbz #511021)

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6c9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild
