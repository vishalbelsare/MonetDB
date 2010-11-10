%define name MonetDB5-server
%define version 5.23.0
%{!?buildno: %define buildno %(date +%Y%m%d)}
%define release %{buildno}%{?dist}%{?oid32:.oid32}%{!?oid32:.oid%{bits}}

# groups of related archs
%define all_x86 i386 i586 i686

%ifarch %{all_x86}
%define bits 32
%else
%define bits 64
%endif

# buildsystem is set to 1 when building an rpm from within the build
# directory; it should be set to 0 (or not set) when building a proper
# rpm
%{!?buildsystem: %define buildsystem 0}

Name: %{name}
Version: %{version}
Release: %{release}
Summary: MonetDB - Monet Database Management System
Vendor: MonetDB BV <info@monetdb.org>

Group: Applications/Databases
License:   MPL - http://monetdb.cwi.nl/Legal/MonetDBLicense-1.1.html
URL: http://monetdb.cwi.nl/
Source: http://dev.monetdb.org/downloads/sources/Oct2010/MonetDB5-server-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

%{!?_with_raptor: %{!?_without_raptor: %define _with_raptor --with-raptor}}

Requires(pre): shadow-utils
BuildRequires: pcre-devel
BuildRequires: libxml2-devel

# when we want MonetDB to run as system daemon, we need this
# also see the scriptlets below
# the init script should implement start, stop, restart, condrestart, status
# Requires(post): /sbin/chkconfig
# Requires(preun): /sbin/chkconfig
# Requires(preun): /sbin/service
# Requires(postun): /sbin/service

%define builddoc 0

Requires: MonetDB-client >= 1.40
#                           ^^^^
# Maintained via vertoo. Please don't modify by hand!
# Contact MonetDB-developers@lists.sourceforge.net for details and/or assistance.
%if !%{?buildsystem}
BuildRequires: MonetDB-devel >= 1.40
#                               ^^^^
# Maintained via vertoo. Please don't modify by hand!
# Contact MonetDB-developers@lists.sourceforge.net for details and/or assistance.
BuildRequires: MonetDB-client-devel >= 1.40
#                                      ^^^^
# Maintained via vertoo. Please don't modify by hand!
# Contact MonetDB-developers@lists.sourceforge.net for details and/or assistance.
%endif

%if %{?_with_raptor:1}%{!?_with_raptor:0}
%package rdf
Summary: MonetDB RDF interface
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}
BuildRequires: raptor-devel >= 1.4.16
%endif

%package devel
Summary: MonetDB development package
Group: Applications/Databases
Requires: %{name} = %{version}-%{release}
%if %{?_with_raptor:1}%{!?_with_raptor:0}
Requires: %{name}-rdf = %{version}-%{release}
%endif
Requires: MonetDB-devel
Requires: MonetDB-client-devel
Requires: libxml2-devel

%description
MonetDB is a database management system that is developed from a
main-memory perspective with use of a fully decomposed storage model,
automatic index management, extensibility of data types and search
accelerators, SQL- and XML- frontends.

This package contains the MonetDB5 server component.  You need this
package if you want to work using the MAL language, or if you want to
use the SQL frontend (in which case you need MonetDB-SQL-server5 as
well).

%if %{?_with_raptor:1}%{!?_with_raptor:0}
%description rdf
MonetDB is a database management system that is developed from a
main-memory perspective with use of a fully decomposed storage model,
automatic index management, extensibility of data types and search
accelerators, SQL- and XML- frontends.

This package contains the MonetDB5 RDF module.
%endif

%description devel
MonetDB is a database management system that is developed from a
main-memory perspective with use of a fully decomposed storage model,
automatic index management, extensibility of data types and search
accelerators, SQL- and XML- frontends.

This package contains the files needed to develop with MonetDB5.

%prep
rm -rf $RPM_BUILD_ROOT

%setup -q -n MonetDB5-server-%{version}

%build

%configure \
	--enable-strict=no \
	--enable-assert=no \
	--enable-debug=no \
	--enable-optimize=yes \
	--enable-bits=%{bits} \
	%{?oid32:--enable-oid32} \
	%{?comp_cc:CC="%{comp_cc}"} \
	%{?_with_raptor} %{?_without_raptor}

make

%install
rm -rf $RPM_BUILD_ROOT

make install DESTDIR=$RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/MonetDB
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/MonetDB5/dbfarm
# insert example db here!

# cleanup stuff we don't want to install
find $RPM_BUILD_ROOT -name .incs.in -print -o -name \*.la -print | xargs rm -f
rm -rf $RPM_BUILD_ROOT%{_libdir}/MonetDB5/Tests/*

find $RPM_BUILD_ROOT%{_libdir}/MonetDB5 \( -name \*.mal -o -name \*.so\* \) ! -name '*rdf*' -print | sed "s|^$RPM_BUILD_ROOT||" > lib-files

%pre
getent group monetdb >/dev/null || groupadd -r monetdb
getent passwd monetdb >/dev/null || \
useradd -r -g monetdb -d %{_localstatedir}/MonetDB -s /sbin/nologin \
    -c "MonetDB Server" monetdb
exit 0

%post
/sbin/ldconfig

# when we want MonetDB to run as system daemon, we need this
# # This adds the proper /etc/rc*.d links for the script
# /sbin/chkconfig --add monetdb5

# %preun
# if [ $1 = 0 ]; then
# 	/sbin/service monetdb5 stop >/dev/null 2>&1
# 	/sbin/chkconfig --del monetdb5
# fi

%postun
/sbin/ldconfig

# when we want MonetDB to run as system daemon, we need this
# if [ "$1" -ge "1" ]; then
# 	/sbin/service monetdb5 condrestart >/dev/null 2>&1 || :
# fi

%clean
rm -fr $RPM_BUILD_ROOT

%files -f lib-files
%defattr(-,root,root)
%{_bindir}/mserver5
%{_bindir}/Mbeddedmal

%{_libdir}/*.so.*
%dir %{_libdir}/MonetDB5
%dir %{_libdir}/MonetDB5/lib
%dir %{_libdir}/MonetDB5/autoload

%attr(750,monetdb,monetdb) %dir %{_localstatedir}/MonetDB
%attr(2770,monetdb,monetdb) %dir %{_localstatedir}/MonetDB5
%attr(2770,monetdb,monetdb) %dir %{_localstatedir}/MonetDB5/dbfarm

%config(noreplace) %{_sysconfdir}/monetdb5.conf
%{_mandir}/man5/monetdb5.conf.5.gz

%if %{?_with_raptor:1}%{!?_with_raptor:0}
%files rdf
%{_libdir}/MonetDB5/rdf.mal
%{_libdir}/MonetDB5/lib/lib_rdf.so*
%{_libdir}/MonetDB5/autoload/*_rdf.mal
%endif

%files devel
%defattr(-,root,root)
%{_bindir}/monetdb5-config
%dir %{_includedir}/MonetDB5
%dir %{_includedir}/MonetDB5/atoms
%dir %{_includedir}/MonetDB5/compiler
%dir %{_includedir}/MonetDB5/crackers
%dir %{_includedir}/MonetDB5/kernel
%dir %{_includedir}/MonetDB5/mal
%dir %{_includedir}/MonetDB5/optimizer
%dir %{_includedir}/MonetDB5/scheduler
%dir %{_includedir}/MonetDB5/rdf
%dir %{_includedir}/MonetDB5/tools
%{_includedir}/MonetDB5/*/*.[hcm]
%{_libdir}/*.so
%{_libdir}/pkgconfig/monetdb-embeddedclient.pc
%{_libdir}/pkgconfig/monetdb-mal.pc

%changelog
* Wed Nov 10 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.22.1-20101110
- Rebuilt.

* Tue Nov 09 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.22.1-20101109
- Rebuilt.

* Fri Nov 05 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.22.1-20101105
- Rebuilt.

* Fri Oct 29 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.22.1-20101029
- Rebuilt.

* Wed Oct 27 2010 Fabian Groffen <fabian@cwi.nl> - 5.22.1-20101029
- Resolved a problem with leaking threads, eventually causing new
  connections to the server to hang, bug #2700

* Mon Aug 30 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.22.1-20101029
- When attempting to insert incorrect UTF-8 sequences in a COPY INTO
  statement, the error message was truncated.  This is now fixed.
  Bug 2575.

* Tue Aug 24 2010 mk@cwi.nl - 5.22.1-20101029
- Debugging the optimizer pipeline The best way is to use mdb.traceOptimizer(str)
  and inspect the information gathered during the optimization phase.
  Several optimizers produce more intermediate information, which may
  shed light on the details.  The optDebug bitvector controls their
  output. It can be set to a pipeline or a comma separated list of
  optimizers you would like to trace. It is a server wide property and
  can not be set dynamically, as it is intended for internal use.

* Tue Aug 24 2010 Stefan Manegold <Stefan.Manegold@cwi.nl> - 5.22.1-20101029
- Added "sequential_pipe" SQL optimizer pipeline that is (and should be kept!)
  identical to the default pipeline, except that optimizers mitosis & dataflow
  are omitted.

* Tue Aug 24 2010 Stefan Manegold <Stefan.Manegold@cwi.nl> - 5.22.1-20101029
- Added "no_mitosis_pipe" SQL optimizer pipeline that is (and should be kept!)
  identical to the default pipeline, except that optimizer mitosis is omitted.

* Tue Aug 24 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.5-20100824
- Rebuilt.

* Tue Aug 24 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.5-20100824
- Fixed a crash when calculating certain aggregates on platforms where
  non-aligned data access is not allowed (e.g. Sparc).

* Mon Aug 23 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.5-20100823
- Rebuilt.

* Fri Aug 20 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.5-20100823
- A bug was fixed where on 32 bit systems (or 64 bit systems using 32 bit
  OIDs), values were sometimes written as 32 bits but read as 64 bits.
  This fixes bugs 2644 and 2654.

* Thu Aug 19 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.5-20100823
- If extensions such as SQL and GEOM are properly installed, they are
  loaded automatically when mserver5 starts.  This fixes bug 2522.

* Fri Jul 30 2010 Niels Nes <niels@cwi.nl> - 5.20.5-20100823
- Fixed bug 2557. There was a bug in the mergetable optimizer which was
  triggered by multi column (at least 32 columns).

* Wed Jul 28 2010 Martin Kersten <mk@cwi.nl> - 5.20.5-20100823
- Added missing multiplex version of MAL str.stringlength().
  This improves performance of SQL length().

* Tue Jul 27 2010 Martin Kersten <mk@cwi.nl> - 5.20.5-20100823
- Protect dataflow against multi-assignments.
  This fixes bugs 2626 & 2614.

* Thu Jul 22 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.5-20100823
- Slight change to Fedora, Debian, Ubuntu installers: the database
  directory now has the group setuid bit set so that new databases
  inherit the group ownership (monetdb).

* Thu Jul 15 2010 Stefan Manegold <Stefan.Manegold@cwi.nl> - 5.20.5-20100823
- Restored genuine original mitosis logic by disabling
  incorrect octopus dominance (even when octopus was not
  enabled); basically a selective back-port of changesets
  http://dev.monetdb.org/hg/MonetDB/rev/2a358751a4b6
  http://dev.monetdb.org/hg/MonetDB/rev/692eff15bea0 from the default
  branch. This fixes bug 2596.

* Tue Jul 13 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.3-20100713
- Rebuilt.

* Mon Jul 12 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.3-20100713
- Fixed bug 2597: This bug manifested itself in rank queries in SQL
  but was a bug in the mergetable optimizer.

* Mon Jul 12 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.3-20100712
- Rebuilt.

* Fri Jul 09 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.3-20100709
- Rebuilt.

* Thu Jul 01 2010 Fabian Groffen <fabian@cwi.nl> - 5.20.3-20100706
- Return a correct URI for local connection from Sabaoth when the
  connection is a UNIX domain socket.  Partial fix for bug #2567.

* Wed Jun 30 2010 Stefan Manegold <Stefan.Manegold@cwi.nl> - 5.20.3-20100706
- various performance fixes in grouping and grouped aggregation code
  (MonetDB5/src/modules/kernel/group.mx,
  MonetDB5/src/modules/kernel/aggr*.mx) to reduce the execution time
  the following query that mimics a two-column primary key check over
  the ~5 billion tuple "neighbors" table of the Skyserver database
  from 26 hours to 1.5 hours (on a 64 GB machine): SELECT count(c),
  sum(c), min(c), max(c) FROM (SELECT count(*) AS c FROM "neighbors"
  GROUP BY "objID","NeighborObjID") AS t;

* Wed Jun 30 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100630
- Rebuilt.

* Fri Jun 25 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100625
- Rebuilt.

* Wed Jun 23 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100625
- When libxml2 is available, the XML module is automatically loaded.

* Tue Jun 22 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100622
- Rebuilt.

* Fri Jun 18 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100618
- Rebuilt.

* Mon May 31 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100618
- Updated Vendor information.

* Wed May 19 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.20.1-20100618
- Created a new RPM MonetDB5-server-rdf for the optional MonetDB/RDF
  module.

* Sun May  2 2010 Martin Kersten <martin.kersten@cwi.nl> - 5.20.1-20100618
- Added the Z-order module to simplify future manipulation of arrays.

* Sat May  1 2010 Stefan Manegold <manegold@cwi.nl> - 5.20.1-20100618
- fixed BUG #2994521 "mat.slice unable to cope with only empty BAT
  arguments" by making MATpackSliceInternal() handle empty input BATs
  correctly

* Tue Apr 20 2010 Martin Kersten <martin.kersten@cwi.nl> - 5.20.1-20100618
- Select <col> from <t> limit <n> has been improved by introducing
  mat.slice().

* Tue Apr 20 2010 Stefan Manegold <manegold@cwi.nl> - 5.20.1-20100618
- Made compilation of "testing" (and "java") independent of MonetDB.
  This is mainly for Windows, but also on other systems, "testing" can
  now be built independently of (and hence before) "MonetDB".  Files
  that mimic configure functionality on Windows were moved from
  "MonetDB" to "buildtools"; hence, this affects all packages on
  Windows, requiring a complete rebuild from scratch on Windows.
  getopt() support in testing has changed; hence, (most probably)
  requiring a rebuild from scratch of testing on other systems.

* Tue Apr 20 2010 Stefan Manegold <manegold@cwi.nl> - 5.20.1-20100618
- Implemented build directory support for Windows, i.e., like on
  Unix/Linux also on Windows we can now build in a separate build
  directory as alternative to ...\<package>\NT, and thus keep the latter
  clean from files generated during the build.  On Windows, the build
  directory must be a sibling of ...\<package>\NT .

* Tue Apr 20 2010 Martin Kersten <martin.kersten@cwi.nl> - 5.20.1-20100618
- The MAL debugger list command has been extended with an optional
  hash '#', which produces line numbers for each of reference and
  analysis of variable span.
- The dataflow scheduler has been revamped to allow for more
  parallelism to be exploited.
- The garbage collection administration has been changed. Every
  variable record now comes with an end-of-life field (eolife), which
  denotes the instruction whereafter the BAT variable reference
  counter can be decremented. The garbage collector is never called
  automagically on MAL functions, because there may be other pressing
  needs to retain them. This means that MAL functions defined and used
  in the context of SQL, and which are not inlined, may cause a
  leakage.  The garbage collection has become part of each interpreter
  step.  The new approach makes the SQL/MAL plans half the size as
  before.

* Tue Apr 20 2010 Fabian Groffen <fabian@cwi.nl> - 5.20.1-20100618
- Removed stethoscope from MonetDB5 sources.  New location is in the
  clients repository.

* Tue Apr 20 2010 Martin Kersten <mk@cwi.nl> - 5.20.1-20100618
- Added the compression optimizer as an example of how to gain access
  to foreign file formats deep down in the kernel and transfer them
  just in time into a temporary BAT.

* Tue Apr 20 2010 Fabian Groffen <fabian@cwi.nl> - 5.20.1-20100618
- Renamed configure argument --with-console to --enable-console.
  Default remains console being enabled.

* Tue Apr 20 2010 Martin Kersten <mk@cwi.nl> - 5.20.1-20100618
- Fixed cleaning the user module context upon session end.
  Fixes bug #2956664

* Tue Apr 20 2010 Fabian Groffen <fabian@cwi.nl> - 5.20.1-20100618
- The config variable mapi_usock can now be used to instruct the
  server to listen for connections on a local UNIX domain socket on
  UNIX-like systems.

* Tue Apr 20 2010 Martin Kersten <mk@cwi.nl> - 5.20.1-20100618
- The MAL interpreter has been extended with an operation admission
  policy to control the memory claims of all concurrent running
  interpreters. Instructions are hold up unto there is sufficient
  resource or the query plan can not avoid its execution anymore.
- The join path optimizer has been extended with searching for join*,
  semijoin*, and leftjoin* paths. Furthermore, it avoids duplicate
  work by factoring out all common simple join paths.

* Tue Apr 20 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.18.5-20100420
- Rebuilt.

* Mon Mar 22 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.18.3-20100322
- Rebuilt.

* Thu Mar 18 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.18.3-20100322
- Fixed a race condition that could occur if many clients were
  connecting and disconnecting.

* Wed Feb 24 2010 Sjoerd Mullender <sjoerd@acm.org> - 5.18.1-20100224
- Rebuilt.

* Sun Feb 21 2010 Martin Kersten <mk@(none)> - 5.18.1-20100223
- The MonetDB 5 code base underwent a series of small/medium changes:
  - Solving name conflicts with external libraries in mal_box.
  - Dependency graph generation in MAL debugger fixed.
  - Code hardening against out of memory errors and based on Coverity
    checks.
  - Recycler improved to deal with SQL plans from different sessions.
  - Profiler extended to report the argument types, user, and thread
    id.
  - MAL interpreter reports an event before and after the instruction.
  - Dataflow also allowed for updates on temporary BATs.
  - Reorder optimizer better respects the dataflow.
  - All update instructions return their target to mark the dataflow.
  - Clean up of (bat)calc module.
  - Packing pieces together simplified and speed up.
- The MAL interpreter has been extended with an operator admission
  scheme, which is active during parallel execution. It blocks threads
  if the total amount of memory needed for the operator can not be
  claimed. Only if there is one operation left to execute, it won't
  block. The admission level is controlled by a threshold, which is
  set to 90% of the physical memory.

* Sun Jan 10 2010 Martin Kersten <mk@> - 5.18.1-20100223
- The ilike[u]select operations has been included in the repertoire
  recognized by the mergetable optimizer for push through of
  selections.
- The joinpath optimizer has been extended with recognition of the
  leftjoin.  This way, series of leftjoin operations can be optimized
  by looking at the smallest starting point.
- Introduced a dictionary encoding option to the optimizer pipeline.
  Encoding is initiated with a SQL call compress(tablename).

* Sun Nov 15 2009 Fabian Groffen <fabian@cwi.nl> - 5.18.1-20100223
- Removed the ability to redirect to other running databases in the
  same dbfarm.  This functionality has been taken over completely by
  merovingian, and only results in confusement these days, bug
  #2891191.
- Added --enable-console configure argument, defaulting to 'yes' for
  now.  Disabling the server console increases security by avoiding
  local access exploits.  This is not the default since our Testing
  setup cannot deal with a console-less server yet.

* Tue Nov  3 2009 Fabian Groffen <fabian@cwi.nl> - 5.18.1-20100223
- Report detected amount of main memory and cpu cores in output of
  `mserver5 --version`.

