# Supported targets: el9

%define nagios_version 4.4.10
%define livestatus_version 1.6.0p30

Name: nagios4z
Version: %{nagios_version}
Release: 2%{?dist}.zenetys

Summary: Host/service/network monitoring program
Group: Applications/System
License: GPLv2
URL: https://www.nagios.org/projects/nagios-core/

# nagios
Source0: https://github.com/NagiosEnterprises/nagioscore/archive/nagios-%{nagios_version}.tar.gz

BuildRequires: gcc
BuildRequires: openssl-devel
BuildRequires: procps-ng
BuildRequires: s-nail
BuildRequires: systemd
BuildRequires: which

# epel comptability
Provides: nagios-common
Provides: user(nagios)
Provides: group(nagios)
Obsoletes: nagios-common

# livestatus
Source100: https://github.com/tribe29/checkmk/archive/v%{livestatus_version}.tar.gz
Patch100: livestatus-1.6.0p30-build.patch
Patch101: livestatus-1.6.0p30-timeperiods-cache-bad-log.patch

BuildRequires: autoconf
BuildRequires: automake
BuildRequires: gcc-g++
BuildRequires: asio-devel
BuildRequires: libstdc++-static
BuildRequires: re2-devel

%description
Nagios is an application, system and network monitoring application.
It can escalate problems by email, pager or any other medium. It is
also useful for incident or SLA reporting.

Nagios is written in C and is designed as a background process,
intermittently running checks on various services that you specify.

%prep
# nagios
%setup -c
cd nagioscore-nagios-%{nagios_version}
patch -p0 < contrib/epel-patches/nagios-0009-fix-localstatedir-for-linux.patch
patch -p0 < contrib/epel-patches/nagios-0010-remove-information-leak.patch
cd ..

# livestatus
%setup -T -D -a 100
cd checkmk-%{livestatus_version}
%patch100 -p1
%patch101 -p1
cd ..

%build
# nagios
cd nagioscore-nagios-%{nagios_version}
%configure \
    --prefix=%{_datadir}/nagios \
    --exec-prefix=%{_localstatedir}/lib/nagios \
    --libdir=%{_libdir}/nagios \
    --bindir=%{_sbindir} \
    --datadir=%{_datadir}/nagios/html \
    --enable-nerd \
    --enable-event-broker \
    --libexecdir=%{_libdir}/nagios/plugins \
    --localstatedir=%{_localstatedir} \
    --with-checkresult-dir=%{_localstatedir}/spool/nagios/checkresults \
    --with-cgibindir=%{_libdir}/nagios/cgi-bin \
    --sysconfdir=%{_sysconfdir}/nagios \
    --with-cgiurl=/nagios/cgi-bin \
    --with-command-user=nagios \
    --with-command-group=nagios \
    --with-gd-lib=%{_libdir} \
    --with-gd-inc=%{_includedir} \
    --with-htmlurl=/nagios \
    --with-lockfile=%{_rundir}/nagios/nagios.pid \
    --with-mail=/usr/bin/mail \
    --with-init-type=systemd \
    --with-initdir=%{_unitdir} \
    --with-nagios-user=nagios \
    --with-nagios-grp=nagios \
#end-of-configure
%make_build all
cd ..

# livestatus
cd checkmk-%{livestatus_version}
autoreconf -fi
%configure \
    --with-nagios4 \
    --with-re2 \
#end-of-configure
cd livestatus/src
%make_build unixcat
%make_build livestatus.o
cd ../../..

%install
# nagios
cd nagioscore-nagios-%{nagios_version}
make_install_opts=( 'DESTDIR=%{buildroot}' 'INSTALL=install -p' INIT_OPTS= INSTALL_OPTS= COMMAND_OPTS= )
make install-unstripped "${make_install_opts[@]}"
make install-init "${make_install_opts[@]}"
make install-commandmode "${make_install_opts[@]}"
make install-exfoliation "${make_install_opts[@]}"
make install-config "${make_install_opts[@]}"
# bundled sample configuration goes in share directory
install -d -m 0755 %{buildroot}/%{_datadir}/nagios/sample-config
mv %{buildroot}/%{_sysconfdir}/nagios/* %{buildroot}/%{_datadir}/nagios/sample-config/
# nagios goes to sbin, nagiostats to bin
install -d -m 0755 %{buildroot}/%{_bindir}
mv %{buildroot}/{%{_sbindir},%{_bindir}}/nagiostats
# bad perms from make install
chmod 0755 %{buildroot}/%{_sysconfdir}/nagios
chmod 0755 %{buildroot}/%{_bindir}/nagiostats
chmod 0755 %{buildroot}/%{_sbindir}/nagios
chmod 0644 %{buildroot}/%{_unitdir}/nagios.service
chmod 0755 %{buildroot}/%{_libdir}/nagios/cgi-bin
chmod 0755 %{buildroot}/%{_libdir}/nagios/cgi-bin/*.cgi
chmod 00755 %{buildroot}/%{_localstatedir}/spool/nagios/checkresults
find %{buildroot}/%{_datadir}/nagios/{html,sample-config} -type d -exec chmod 0755 {} +
find %{buildroot}/%{_datadir}/nagios/{html,sample-config} -type f -exec chmod 0644 {} +
# other bits not installed by make install
install -d -m 0755 %{buildroot}/%{_sysconfdir}/nagios/conf.d
install -d -m 0755 %{buildroot}/%{_libdir}/nagios/plugins{,/eventhandlers}
install -d -m 0755 %{buildroot}/%{_localstatedir}/log/nagios/archives
install -d -m 0755 %{buildroot}/%{_rundir}/nagios
install -d -m 0755 %{buildroot}/%{_localstatedir}/spool/nagios/cmd
install -D -m 0644 -p contrib/epel-patches/nagios.logrotate %{buildroot}/%{_sysconfdir}/logrotate.d/nagios
install -D -m 0644 -p contrib/epel-patches/nagios.tmpfiles.conf %{buildroot}/%{_tmpfilesdir}/nagios.conf
# shipped defaults configuration uses the service tmpfs
echo 'D /run/nagios/checkresults 0755 nagios nagios -' >> %{buildroot}/%{_tmpfilesdir}/nagios.conf
echo 'D /run/nagios/tmp 0755 nagios nagios -' >> %{buildroot}/%{_tmpfilesdir}/nagios.conf
# include headers
install -D -m 0644 -p -t %{buildroot}%{_includedir}/nagios/ include/*.h
install -D -m 0644 -p -t %{buildroot}/%{_includedir}/nagios/lib/ lib/*.h
install -D -m 0644 -p -t %{buildroot}/%{_libdir}/nagios/ lib/libnagios.a
# doc, license
install -D -m 0644 -p -t ../doc/nagios/ Changelog INSTALLING README.md UPGRADING
install -D -m 0644 -p -t ../license/nagios/ LICENSE
cd ..

# livestatus
cd checkmk-%{livestatus_version}
install -D -m 0755 -p livestatus/src/unixcat %{buildroot}/%{_bindir}/
install -D -m 0755 -p livestatus/src/livestatus.o %{buildroot}/%{_libdir}/nagios/
# doc, license
install -D -m 0644 -p -t ../doc/livestatus/ AUTHORS
install -D -m 0644 -p -t ../license/livestatus/ COPYING
cd ..

%pre
if ! getent group nagios >/dev/null; then
    groupadd -r nagios
fi
if ! getent passwd nagios >/dev/null; then
    useradd -r -g nagios -d %{_localstatedir}/spool/nagios -s /sbin/nologin nagios
fi

%post
%systemd_post nagios.service

%preun
%systemd_preun nagios.service

%postun
%systemd_postun_with_restart nagios.service

%files
%defattr(-, root, root, -)

%doc doc/*
%license license/*

%{_sysconfdir}/nagios
%config(noreplace) %{_sysconfdir}/logrotate.d/nagios
%ghost %config(noreplace) %{_sysconfdir}/nagios/nagios.cfg
%ghost %config(noreplace) %{_sysconfdir}/nagios/resource.cfg

%{_includedir}/nagios
%{_libdir}/nagios
%{_bindir}/nagiostats
%{_bindir}/unixcat
%{_datadir}/nagios
%{_sbindir}/nagios
%{_tmpfilesdir}/nagios.conf
%{_unitdir}/nagios.service

%attr(-, nagios, nagios) %dir %{_localstatedir}/spool/nagios/cmd
%attr(-, nagios, nagios) %dir %{_localstatedir}/log/nagios
%attr(-, nagios, nagios) %dir %{_localstatedir}/log/nagios/archives
%attr(-, nagios, nagios) %dir %{_localstatedir}/spool/nagios
%attr(-, nagios, nagios) %dir %{_localstatedir}/spool/nagios/checkresults
%attr(-, nagios, nagios) %dir %{_rundir}/nagios
