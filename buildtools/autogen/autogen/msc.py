# The contents of this file are subject to the MonetDB Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://monetdb.cwi.nl/Legal/MonetDBLicense-1.1.html
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
#
# The Original Code is the MonetDB Database System.
#
# The Initial Developer of the Original Code is CWI.
# Portions created by CWI are Copyright (C) 1997-July 2008 CWI.
# Copyright August 2008-2011 MonetDB B.V.
# All Rights Reserved.

import string
import os
import re

# the text that is put at the top of every generated Makefile.msc
MAKEFILE_HEAD = '''
## Use: nmake -f makefile.msc install

# Nothing much configurable below

'''

#automake_ext = ['c', 'h', 'y', 'l', 'glue.c']
automake_ext = ['c', 'h', 'tab.c', 'tab.h', 'yy.c', 'glue.c', 'proto.h', 'py.i', 'pm.i', '']
automake_ext.extend(['cc', 'yy', 'll'])  # C++

def split_filename(f):
    base = f
    ext = ""
    if string.find(f, ".") >= 0:
        return string.split(f, ".", 1)
    return base, ext

def rsplit_filename(f):
    base = f
    ext = ""
    s = string.rfind(f, ".")
    if s >= 0:
        return f[:s], f[s+1:]
    return base, ext

def msc_basename(f):
    # return basename (i.e. just the file name part) of a path, no
    # matter which directory separator was used
    return string.split(string.split(f, '/')[-1], '\\')[-1]

def msc_dummy(fd, var, values, msc):
    res = fd

def msc_list2string(l, pre, post):
    res = ""
    for i in l:
        res = res + pre + i + post
    return res

def create_dir(fd, v, n, i):
    # Stupid Windows/nmake cannot cope with single-letter directory
    # names; apparently, it treats them as drive-letters, unless we
    # explicitely call them ".\?".
    if len(v) == 1:
        vv = '.\\%s' % v
    else:
        vv = v
    fd.write('%s-%d-all: "%s-%d-dir" "%s-%d-Makefile"\n' % (n, i, n, i, n, i))
    fd.write('\t$(CD) "%s" && $(MAKE) /nologo $(MAKEDEBUG) "prefix=$(prefix)" "bits=$(bits)" all \n' % vv)
    fd.write('%s-%d-dir: \n\tif not exist "%s" $(MKDIR) "%s"\n' % (n, i, vv, vv))
    fd.write('%s-%d-Makefile: "$(SRCDIR)\\%s\\Makefile.msc"\n' % (n, i, v))
    fd.write('\t$(INSTALL) "$(SRCDIR)\\%s\\Makefile.msc" "%s\\Makefile"\n' % (v, v))
    fd.write('%s-%d-check:\n' % (n, i))
    fd.write('\t$(CD) "%s" && $(MAKE) /nologo $(MAKEDEBUG) "prefix=$(prefix)" "bits=$(bits)" check\n' % vv)

    fd.write('%s-%d-install:\n' % (n, i))
    fd.write('\t$(CD) "%s" && $(MAKE) /nologo $(MAKEDEBUG) "prefix=$(prefix)" "bits=$(bits)" install\n' % vv)

def empty_dir(fd, n, i):
    fd.write('%s-%d-all:\n' % (n, i))
    fd.write('%s-%d-check:\n' % (n, i))
    fd.write('%s-%d-install:\n' % (n, i))

def create_subdir(fd, dir, i):
    res = ""
    if string.find(dir, "?") > -1:
        parts = string.split(dir, "?")
        if len(parts) == 2:
            dirs = string.split(parts[1], ":")
            fd.write("!IFDEF %s\n" % parts[0])
            if len(dirs) > 0 and string.strip(dirs[0]) != "":
                create_dir(fd, dirs[0], parts[0], i)
            else:
                empty_dir(fd, parts[0], i)
            if len(dirs) > 1 and string.strip(dirs[1]) != "":
                fd.write("!ELSE\n")
                create_dir(fd, dirs[1], parts[0], i)
            else:
                fd.write("!ELSE\n")
                empty_dir(fd, parts[0], i)
            fd.write("!ENDIF\n")
        res = '%s-%d' % (parts[0], i)
    else:
        create_dir(fd, dir, dir, i)
        res = '%s-%d' % (dir, i)
    return res

def msc_subdirs(fd, var, values, msc):
    # to cope with conditional subdirs:
    dirs = []
    i = 0
    nvalues = []
    for dir in values:
        i = i + 1
        val = create_subdir(fd, dir, i)
        if val:
            nvalues.append(val)

    fd.write("all-recursive: %s\n" % msc_list2string(nvalues, '"', '-all" '))
    fd.write("check-recursive: %s\n" % msc_list2string(nvalues, '"', '-check" '))
    fd.write("install-recursive: %s\n" % msc_list2string(nvalues, '"', '-install" '))

def msc_assignment(fd, var, values, msc):
    o = ""
    for v in values:
        o = o + " " + string.replace(v, '/', '\\')
    if var[0] != '@':
        fd.write("%s = %s\n" % (var, o))

def msc_cflags(fd, var, values, msc):
    o = ""
    for v in values:
        o = o + " " + v
    fd.write("%s = $(%s) %s\n" % (var.replace('-','_'), var.replace('-','_'), o))

def msc_extra_dist(fd, var, values, msc):
    for i in values:
        msc['EXTRA_DIST'].append(i)

def msc_extra_headers(fd, var, values, msc):
    for i in values:
        msc['HDRS'].append(i)

def msc_libdir(fd, var, values, msc):
    msc['LIBDIR'] = values[0]

def msc_mtsafe(fd, var, values, msc):
    fd.write("CFLAGS=$(CFLAGS) $(thread_safe_flag_spec)\n")

def msc_add_srcdir(path, msc, prefix =""):
    dir = path
    if dir[0] == '$':
        return ""
    elif not os.path.isabs(dir):
        dir = "$(SRCDIR)/" + dir
    else:
        return ""
    return prefix+string.replace(dir, '/', '\\')

def msc_translate_dir(path, msc):
    dir = path
    rest = ""
    if string.find(path, '/') >= 0:
        dir, rest = string.split(path, '/', 1)
    if dir == "top_builddir":
        dir = "$(TOPDIR)"
    elif dir == "top_srcdir":
        dir = "$(TOPDIR)/.."
    elif dir == "builddir":
        dir = "."
    elif dir == "srcdir":
        dir = "$(SRCDIR)"
    elif dir in ('bindir', 'builddir', 'datadir', 'includedir', 'infodir',
                 'libdir', 'libexecdir', 'localstatedir', 'mandir',
                 'oldincludedir', 'pkgbindir', 'pkgdatadir', 'pkgincludedir',
                 'pkglibdir', 'pkglocalstatedir', 'pkgsysconfdir', 'sbindir',
                 'sharedstatedir', 'srcdir', 'sysconfdir', 'top_builddir',
                 'top_srcdir', 'prefix'):
        dir = "$("+dir+")"
    if rest:
        dir = dir+ "\\" + rest
    return string.replace(dir, '/', '\\')

def msc_translate_file(path, msc):
    if os.path.isfile(os.path.join(msc['cwd'], path)):
        return "$(SRCDIR)\\" + path
    return path

def msc_space_sep_list(l):
    res = ""
    for i in l:
        res = res + " " + i
    return res + "\n"

def msc_find_srcs(target, deps, msc):
    base, ext = split_filename(target)
    f = target
    pf = f
    while ext != "h" and deps.has_key(f):
        f = deps[f][0]
        b, ext = split_filename(f)
        if ext in automake_ext:
            pf = f
    # built source if has dep and ext != cur ext
    if deps.has_key(pf) and pf not in msc['BUILT_SOURCES']:
        pfb, pfext = split_filename(pf)
        sfb, sfext = split_filename(deps[pf][0])
        if sfext != pfext:
            msc['BUILT_SOURCES'].append(pf)
    return pf

def msc_find_hdrs(target, deps, hdrs):
    base, ext = split_filename(target)
    f = target
    pf = f
    while ext != "h" and deps.has_key(f):
        f = deps[f][0]
        b, ext = split_filename(f)
        if ext in automake_ext:
            pf = f
    return pf

libno = 0
def msc_additional_libs(fd, name, sep, type, list, dlibs, msc, pref, ext):
    deps = pref+sep+name+ext+": "
    if type == "BIN":
        add = name.replace('-','_')+"_LIBS ="
    elif type == "LIB":
        add = pref+sep+name.replace('-','_')+"_LIBS ="
    else:
        add = name.replace('-','_') + " ="
    cond = ''
    for l in list:
        if '?' in l:
            c, l = l.split('?', 1)
        else:
            c = None
        d = None
        if l == "@LIBOBJS@":
            l = "$(LIBOBJS)"
        # special case (hack) for system libraries
        elif l in ('-lodbc32', '-lodbccp32', '-lversion', '-lshlwapi', '-luser32'):
            l = l[2:] + '.lib'
        elif l[:2] == "-l":
            l = "lib"+l[2:]+".lib"
        elif l[:2] == "-L":
            l = '"/LIBPATH:%s"' % l[2:].replace('/', '\\')
        elif l[0] == "-":
            l = '"%s"' % l
        elif l[0] == '$':
            pass
        elif l[0] != "@":
            lib = msc_translate_dir(l, msc) + '.lib'
            # add quotes if space in name
            # we can't always add quotes since for some weird reason
            # in src\modules\plain you will then have a problem with
            # lib_algebra.lib.
            if ' ' in lib:
                lib = '"%s"' % lib
            l = lib
            d = lib
        else:
            l = None
        if c and l:
            global libno
            v = 'LIB%d' % libno
            libno = libno + 1
            cond += '!IF %s\n%s = %s\n!ELSE\n%s =\n!ENDIF\n' % (c, v, l, v)
            l = '$(%s)' % v
            if d:
                deps = '%s %s' % (deps, l)
        elif d:
            deps = '%s %s' % (deps, d)
        if l:
            add = add + ' ' + l
    # this can probably be removed...
    for l in dlibs:
        if l == "@LIBOBJS@":
            add = add + " $(LIBOBJS)"
        elif l[:2] == "-l":
            add = add + " lib"+l[2:]+".lib"
        elif l[0] in  ("-", "$"):
            add = add + " " + l
        elif l[0] not in  ("@"):
            add = add + " " + msc_translate_dir(l, msc) + ".lib"
            deps = deps + ' "' + msc_translate_dir(l, msc) + '.lib"'
    if cond:
        fd.write(cond)
    if type != "MOD":
        fd.write(deps + "\n")
    fd.write(add + "\n")

def msc_translate_ext(f):
    return string.replace(f, '.o', '.obj')

def msc_find_target(target, msc):
    tree = msc['TREE']
    for t, v in tree.items():
        if type(v) is type({}) and v.has_key('TARGETS'):
            targets = v['TARGETS']
            if target in targets:
                if t == "BINS" or t[0:4] == "bin_":
                    return "BIN", "BIN"
                elif (t[0:4] == "lib_"):
                    return "LIB", string.upper(t[4:])
                elif t == "LIBS":
                    name, ext = split_filename(target)
                    return "LIB", string.upper(name)
    return "UNKNOWN", "UNKNOWN"

def msc_dep(fd, tar, deplist, msc):
    t = msc_translate_ext(tar)
    b, ext = split_filename(t)
    tf = msc_translate_file(t, msc)
    sep = tf + ": "
    _in = []
    for d in deplist:
        if not os.path.isabs(d):
            dep = msc_translate_dir(msc_translate_ext(msc_translate_file(d, msc)), msc)
            if dep[-3:] == '.in':
                if dep not in msc['_IN']:
                    _in.append((d[:-3], dep))
                dep = d[:-3]
            if dep != t:
                fd.write('%s"%s"' % (sep, dep))
                sep = " "
        else:
            print "!WARNING: dropped absolute dependency " + d
    if sep == " ":
        fd.write("\n")
        if tf+'.mx.in' in deplist:
            fd.write('\t$(MX) $(MXFLAGS) -x sh "%s.mx"\n' % tf)
    for x, y in _in:
        # TODO
        # replace this hack by something like configure ...
        fd.write('%s: "%s"\n' % (x, y))
        fd.write('\t$(CONFIGURE) "%s" > "%s"\n' % (y, x))
        msc['_IN'].append(y)
    getsrc = ""
    src = msc_translate_dir(msc_translate_ext(msc_translate_file(deplist[0], msc)), msc)
    if os.path.split(src)[0]:
        getsrc = '\t$(INSTALL) "%s" "%s"\n' % (src, os.path.split(src)[1])
    if ext == "tab.h":
        fd.write(getsrc)
        x, de = split_filename(deplist[0])
        of = b + '.' + de
        of = msc_translate_file(of, msc)
        fd.write('\t$(YACC) $(YFLAGS) "%s"\n' % of)
        fd.write("\t$(DEL) y.tab.c\n")
        fd.write('\t$(MV) y.tab.h "%s.tab.h"\n' % b)
    if ext == "tab.c":
        fd.write(getsrc)
        x, de = split_filename(deplist[0])
        of = b + '.' + de
        of = msc_translate_file(of, msc)
        fd.write('\t$(YACC) $(YFLAGS) "%s"\n' % of)
        fd.write('\t$(FILTER) $(FILTERPREF)"    ;" y.tab.c > "%s.tab.c"\n' % b)
        fd.write("\t$(DEL) y.tab.h\n")
    if ext == "yy.c":
        fd.write(getsrc)
        fd.write('\t$(LEX) $(LFLAGS) "%s.l"\n' % b)
        # either lex.<name>.c or lex.yy.c or lex.$(PARSERNAME).c gets generated
        fd.write('\tif exist lex.%s.c $(MV) lex.%s.c "%s.yy.c.tmp"\n' % (b,b,b))
        fd.write('\tif exist lex.yy.c $(MV) lex.yy.c "%s.yy.c.tmp"\n' % b)
        fd.write('\tif exist lex.$(PARSERNAME).c $(MV) lex.$(PARSERNAME).c "%s.yy.c.tmp"\n' % b)
        fd.write('\techo #include "$(CONFIG_H)" > "%s.yy.c"\n' % b)
        fd.write('\ttype "%s.yy.c.tmp" >> "%s.yy.c"\n' % (b, b))
    if ext == "h" and deplist[0][-3:] == '.yy':
        fd.write(getsrc)
        x, de = split_filename(deplist[0])
        of = b + '.' + de
        of = msc_translate_file(of, msc)
        fd.write('\t$(YACC) $(YFLAGS) "%s"\n' % of)
        fd.write("\t$(DEL) y.tab.c\n")
        fd.write('\t$(MV) y.tab.h "%s.h"\n' % b)
    if ext == "cc" and deplist[0][-3:] == '.yy':
        fd.write(getsrc)
        x, de = split_filename(deplist[0])
        of = b + '.' + de
        of = msc_translate_file(of, msc)
        fd.write('\t$(YACC) $(YFLAGS) "%s"\n' % of)
        fd.write('\t$(FILTER) $(FILTERPREF)"    ;" y.tab.c > "%s.cc"\n' % b)
        fd.write("\t$(DEL) y.tab.h\n")
    if ext == "cc" and deplist[0][-3:] == '.ll':
        fd.write(getsrc)
        fd.write('\t$(LEX) $(LFLAGS) "%s.ll"\n' % b)
        # either lex.<name>.c or lex.yy.c or lex.$(PARSERNAME).c gets generated
        fd.write('\tif exist lex.%s.c $(MV) lex.%s.c "%s.yy.c.tmp"\n' % (b,b,b))
        fd.write('\tif exist lex.yy.c $(MV) lex.yy.c "%s.yy.c.tmp"\n' % b)
        fd.write('\tif exist lex.$(PARSERNAME).c $(MV) lex.$(PARSERNAME).c "%s.yy.c.tmp"\n' % b)
        fd.write('\techo #include "$(CONFIG_H)" > "%s.cc"\n' % b)
        fd.write('\ttype "%s.yy.c.tmp" >> "%s.cc"\n' % (b, b))
    if ext == "glue.c":
        fd.write(getsrc)
        fd.write('\t$(MEL) -c $(CONFIG_H) $(INCLUDES) -o "%s" -glue "%s.m"\n' % (t, b))
    if ext == "proto.h":
        fd.write(getsrc)
        fd.write('\t$(MEL) -c $(CONFIG_H) $(INCLUDES) -o "%s" -proto "%s.m"\n' % (t, b))
    if ext == "mil":
        fd.write(getsrc)
        if b+".tmpmil" in deplist:
            fd.write('\t$(MEL) -c $(CONFIG_H) $(INCLUDES) -mil "%s.m" > "%s.mil"\n' % (b, b))
            fd.write('\ttype "%s.tmpmil" >> "%s.mil"\n' % (b, b))
            fd.write('\tif not exist .libs $(MKDIR) .libs\n')
            fd.write('\t$(INSTALL) "%s.mil" ".libs\\%s.mil"\n' % (b, b))
    if ext in ("obj", "glue.obj", "tab.obj", "yy.obj"):
        target, name = msc_find_target(tar, msc)
        if name[0] == '_':
            name = name[1:]
        if target == "LIB":
            d, dext = split_filename(deplist[0])
            if dext in ("c", "glue.c", "yy.c", "tab.c"):
                # -DCOMPILE_DL_%s is for PHP extensions
                fd.write('\t$(CC) $(CFLAGS) $(%s_CFLAGS) $(GENDLL) -DLIB%s -DCOMPILE_DL_%s -Fo"%s" -c "%s"\n' %
                         (split_filename(msc_basename(src))[0], name, name, t, src))
    if ext == 'py' and deplist[0].endswith('.py.i'):
        fd.write('\t$(SWIG) -python $(SWIGFLAGS) -outdir . -o dummy.c "%s"\n' % src)
        fd.write('\t$(DEL) dummy.c\n')
    if ext == 'py.c' and deplist[0].endswith('.py.i'):
        fd.write('\t$(SWIG) -python $(SWIGFLAGS) -outdir . -o "$@" "%s"\n' % src)
    if ext == 'pm' and deplist[0].endswith('.pm.i'):
        fd.write('\t$(SWIG) -perl $(SWIGFLAGS) -outdir . -o dummy.c "%s"\n' % src)
        fd.write('\t$(DEL) dummy.c\n')
    if ext == 'pm.c' and deplist[0].endswith('.pm.i'):
        fd.write('\t$(SWIG) -perl $(SWIGFLAGS) -outdir . -o "$@" "%s"\n' % src)
    if ext == 'res':
        fd.write("\t$(RC) -fo%s %s\n" % (t, src))

def msc_deps(fd, deps, objext, msc):
    if not msc['DEPS']:
        for t, deplist in deps.items():
            msc_dep(fd, t, deplist, msc)

    msc['DEPS'].append("DONE")

# list of scripts to install
def msc_scripts(fd, var, scripts, msc):

    s, ext = string.split(var, '_', 1);
    ext = [ ext ]
    if scripts.has_key("EXT"):
        ext = scripts["EXT"] # list of extentions

    sd = "bindir"
    if scripts.has_key("DIR"):
        sd = scripts["DIR"][0] # use first name given
    sd = msc_translate_dir(sd, msc)

    for script in scripts['TARGETS']:
        s,ext2 = rsplit_filename(script)
        if not ext2 in ext:
            continue
        if msc['INSTALL'].has_key(script):
            continue
        if os.path.isfile(os.path.join(msc['cwd'], script+'.in')):
            inf = '$(SRCDIR)\\%s.in' % script
            if inf not in msc['_IN']:
                # TODO
                # replace this hack by something like configure ...
                fd.write('%s: "%s"\n' % (script, inf))
                fd.write('\t$(CONFIGURE) "%s" > "%s"\n' % (inf, script))
                msc['_IN'].append(inf)
        elif os.path.isfile(os.path.join(msc['cwd'], script)):
            fd.write('%s: "$(SRCDIR)\\%s"\n' % (script, script))
            fd.write('\t$(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (script, script))
        if scripts.has_key('COND'):
            condname = 'defined(' + ') && defined('.join(scripts['COND']) + ')'
            mkname = script.replace('.', '_').replace('-', '_')
            fd.write('!IF %s\n' % condname)
            fd.write('C_%s = %s\n' % (mkname, script))
            fd.write('!ELSE\n')
            fd.write('C_%s =\n' % mkname)
            fd.write('!ENDIF\n')
            cscript = '$(C_%s)' % mkname
        else:
            cscript = script
            condname = ''
        if not scripts.has_key('NOINST') and not scripts.has_key('NOINST_MSC'):
            msc['INSTALL'][script] = cscript, '', sd, '', condname
        msc['SCRIPTS'].append(cscript)

##    msc_deps(fd, scripts['DEPS'], "\.o", msc)

# return the unique elements of the argument list
def uniq(l):
    try:
        return list(set(l))
    except NameError:                   # presumably set() is unknown
        u = {}
        for x in l:
            u[x] = 1
        return u.keys()

# list of headers to install
def msc_headers(fd, var, headers, msc):

    sd = "includedir"
    if headers.has_key("DIR"):
        sd = headers["DIR"][0] # use first name given
    sd = msc_translate_dir(sd, msc)

    hdrs_ext = headers['HEADERS']
    deps = []
    for d,srcs in headers['DEPS'].items():
        for s in srcs:
            if s in headers['SOURCES']:
                deps.append(d)
                break
    for header in uniq(headers['TARGETS'] + deps):
        h, ext = split_filename(header)
        if ext in hdrs_ext:
            if os.path.isfile(os.path.join(msc['cwd'], header+'.in')):
                inf = '$(SRCDIR)\\%s.in' % header
                if inf not in msc['_IN']:
                    # TODO
                    # replace this hack by something like configure ...
                    fd.write('%s: "%s"\n' % (header, inf))
                    fd.write('\t$(CONFIGURE) "%s" > "%s"\n' % (inf, header))
                    msc['_IN'].append(inf)
            elif os.path.isfile(os.path.join(msc['cwd'], header)):
                fd.write('%s: "$(SRCDIR)\\%s"\n' % (header, header))
##                fd.write('\t$(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (header, header))
##                fd.write('\tif not exist "%s" if exist "$(SRCDIR)\\%s" $(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (header, header, header, header))
                fd.write('\t$(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (header, header))
            if headers.has_key('COND'):
                condname = 'defined(' + ') && defined('.join(headers['COND']) + ')'
                mkname = header.replace('.', '_').replace('-', '_')
                fd.write('!IF %s\n' % condname)
                fd.write('C_%s = %s\n' % (mkname, header))
                fd.write('!ELSE\n')
                fd.write('C_%s =\n' % mkname)
                fd.write('!ENDIF\n')
                cheader = '$(C_%s)' % mkname
            else:
                cheader = header
                condname = ''
            msc['INSTALL'][header] = header, '', sd, '', condname
            msc['SCRIPTS'].append(header)

##    msc_find_ins(msc, headers)
##    msc_deps(fd, headers['DEPS'], "\.o", msc)

def msc_doc(fd, var, docmap, msc):
    docmap['TARGETS']=[]

def msc_binary(fd, var, binmap, msc):

    if type(binmap) == type([]):
        name = var[4:]
        if name == 'SCRIPTS':
            for i in binmap:
                if os.path.isfile(os.path.join(msc['cwd'], i+'.in')):
                    # TODO
                    # replace this hack by something like configure ...
                    fd.write('%s: "$(SRCDIR)\\%s.in"\n' % (i, i))
                    fd.write('\t$(CONFIGURE) "$(SRCDIR)\\%s.in" > "%s"\n' % (i, i))
                elif os.path.isfile(os.path.join(msc['cwd'], i)):
                    fd.write('%s: "$(SRCDIR)\\%s"\n' % (i, i))
                    fd.write('\t$(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (i, i))
                msc['INSTALL'][i] = i, '', '$(bindir)', '', ''
        else: # link
            binmap = binmap[0]
            if '?' in binmap:
                cond, binmap = binmap.split('?', 1)
                condname = 'defined(%s)' % cond
            else:
                cond = condname = ''
            src = binmap[4:]
            if cond:
                fd.write('!IF %s\n' % condname)
            fd.write('%s: "%s"\n' % (name, src))
            fd.write('\t$(CP) "%s" "%s"\n\n' % (src, name))
            if cond:
                fd.write('!ELSE\n')
                fd.write('%s:\n' % name)
                fd.write('!ENDIF\n')
            n_nme, n_ext = split_filename(name)
            s_nme, s_ext = split_filename(src)
            if n_ext  and  s_ext  and  n_ext == s_ext:
                ext = ''
            else:
                ext = '.exe'
            msc['INSTALL'][name] = src + ext, ext, '$(bindir)', '', condname
            msc['SCRIPTS'].append(name)
        return

    if binmap.has_key('MTSAFE'):
        fd.write("CFLAGS=$(CFLAGS) $(thread_safe_flag_spec)\n")

    HDRS = []
    hdrs_ext = []
    if binmap.has_key('HEADERS'):
        hdrs_ext = binmap['HEADERS']

    SCRIPTS = []
    scripts_ext = []
    if binmap.has_key('SCRIPTS'):
        scripts_ext = binmap['SCRIPTS']

    name = var[4:]
    if binmap.has_key("NAME"):
        binname = binmap['NAME'][0]
    else:
        binname = name
    binname2 = binname.replace('-','_').replace('.', '_')

    if binmap.has_key('COND'):
        condname = 'defined(' + ') && defined('.join(binmap['COND']) + ')'
        fd.write('!IF %s\n' % condname)
        fd.write('C_%s_exe = %s.exe\n' % (binname2, binname))
        msc['BINS'].append((binname, '$(C_%s_exe)' % binname2, condname))
    else:
        condname = ''
        if binmap.has_key('NOINST'):
            msc['NBINS'].append((binname, binname, condname))
        else:
            msc['BINS'].append((binname, binname, condname))

    if binmap.has_key("DIR"):
        bd = binmap["DIR"][0] # use first name given
        fd.write("%sdir = %s\n" % (binname2, msc_translate_dir(bd,msc)) );
    else:
        fd.write("%sdir = $(bindir)\n" % binname2);

    binlist = []
    if binmap.has_key("LIBS"):
        binlist = binlist + binmap["LIBS"]
    if binmap.has_key("WINLIBS"):
        binlist = binlist + binmap["WINLIBS"]
    if binlist:
        msc_additional_libs(fd, binname, "", "BIN", binlist, [], msc, '', '.exe')

    srcs = binname2+"_OBJS ="
    for target in binmap['TARGETS']:
        t, ext = split_filename(target)
        if ext == "o":
            srcs = srcs + " " + t + ".obj"
        elif ext == "glue.o":
            srcs = srcs + " " + t + ".glue.obj"
        elif ext == "tab.o":
            srcs = srcs + " " + t + ".tab.obj"
        elif ext == "yy.o":
            srcs = srcs + " " + t + ".yy.obj"
        elif ext == 'def':
            srcs = srcs + ' ' + target
        elif ext == 'res':
            srcs = srcs + " " + t + ".res"
        elif ext in hdrs_ext:
            HDRS.append(target)
        elif ext in scripts_ext:
            if target not in SCRIPTS:
                SCRIPTS.append(target)
    fd.write(srcs + "\n")
    fd.write("%s.exe: $(%s_OBJS)\n" % (binname, binname2))
    fd.write('\t"$(TOPDIR)\\..\\NT\\wincompile.py" $(CC) $(CFLAGS)')
    fd.write(" -Fe%s.exe $(%s_OBJS) /link @<<\n$(%s_LIBS) /subsystem:console /NODEFAULTLIB:LIBC\n<<\n" % (binname, binname2, binname2))
    fd.write("\t$(EDITBIN) $@ /HEAP:1048576,1048576 /LARGEADDRESSAWARE\n");
    fd.write("\tif exist $@.manifest $(MT) -manifest $@.manifest -outputresource:$@;1\n");
    if condname:
        fd.write('!ELSE\n')
        fd.write('C_%s_exe =\n' % binname2)
        fd.write('!ENDIF\n')
    fd.write('\n')

    if SCRIPTS:
        fd.write(binname2+"_SCRIPTS =" + msc_space_sep_list(SCRIPTS))
        msc['BUILT_SOURCES'].append("$(" + binname2 + "_SCRIPTS)")

    if binmap.has_key('HEADERS'):
        for h in HDRS:
            msc['HDRS'].append(h)

    msc_deps(fd, binmap['DEPS'], ".obj", msc)

def msc_bins(fd, var, binsmap, msc):

    HDRS = []
    hdrs_ext = []
    if binsmap.has_key('HEADERS'):
        hdrs_ext = binsmap['HEADERS']

    SCRIPTS = []
    scripts_ext = []
    if binsmap.has_key('SCRIPTS'):
        scripts_ext = binsmap['SCRIPTS']

    name = ""
    if binsmap.has_key("NAME"):
        name = binsmap["NAME"][0] # use first name given
    if binsmap.has_key('MTSAFE'):
        fd.write("CFLAGS=$(CFLAGS) $(thread_safe_flag_spec)\n")

    for binsrc in binsmap['SOURCES']:
        bin, ext = split_filename(binsrc)
        #if ext not in automake_ext:
        msc['EXTRA_DIST'].append(binsrc)

        if binsmap.has_key("DIR"):
            bd = binsmap["DIR"][0] # use first name given
            fd.write("%sdir = %s\n" % (bin.replace('-','_'), msc_translate_dir(bd,msc)) );
        else:
            fd.write("%sdir = $(bindir)\n" % (bin.replace('-','_')) );

        if binsmap.has_key('NOINST'):
            msc['NBINS'].append((bin, bin, ''))
        else:
            msc['BINS'].append((bin, bin, ''))

        if binsmap.has_key(bin + "_LIBS"):
            msc_additional_libs(fd, bin, "", "BIN", binsmap[bin + "_LIBS"], [], msc, '', '.exe')
        else:
            binslist = []
            if binsmap.has_key("LIBS"):
                binslist = binslist + binsmap["LIBS"]
            if binsmap.has_key("WINLIBS"):
                binslist = binslist + binsmap["WINLIBS"]
            if binslist:
                msc_additional_libs(fd, bin, "", "BIN", binslist, [], msc, '', '.exe')

        srcs = bin+"_OBJS ="
        for target in binsmap['TARGETS']:
            t, ext = split_filename(target)
            if t == bin:
                t, ext = split_filename(target)
                if ext == "o":
                    srcs = srcs + " " + t + ".obj"
                elif ext == "glue.o":
                    srcs = srcs + " " + t + ".glue.obj"
                elif ext == "tab.o":
                    srcs = srcs + " " + t + ".tab.obj"
                elif ext == "yy.o":
                    srcs = srcs + " " + t + ".yy.obj"
                elif ext == 'res':
                    srcs = srcs + " " + t + ".res"
                elif ext in hdrs_ext:
                    HDRS.append(target)
                elif ext in scripts_ext:
                    if target not in SCRIPTS:
                        SCRIPTS.append(target)
        fd.write(srcs + "\n")
        fd.write("%s.exe: $(%s_OBJS)\n" % (bin, bin.replace('-','_')))
        fd.write('\t"$(TOPDIR)\\..\\NT\\wincompile.py" $(CC) $(CFLAGS)')
        fd.write(" -Fe%s.exe $(%s_OBJS) /link @<<\n$(%s_LIBS) /subsystem:console /NODEFAULTLIB:LIBC\n<<\n" % (bin, bin.replace('-','_'), bin.replace('-','_')))
        fd.write("\tif exist $@.manifest $(MT) -manifest $@.manifest -outputresource:$@;1\n\n");

    if SCRIPTS:
        fd.write(name.replace('-','_')+"_SCRIPTS =" + msc_space_sep_list(SCRIPTS))
        msc['BUILT_SOURCES'].append("$(" + name.replace('-','_') + "_SCRIPTS)")

    if binsmap.has_key('HEADERS'):
        for h in HDRS:
            msc['HDRS'].append(h)

    msc_deps(fd, binsmap['DEPS'], ".obj", msc)

def msc_mods_to_libs(fd, var, modmap, msc):
    modname = var[:-4]+"LIBS"
    msc_assignment(fd, var, modmap, msc)
    msc_additional_libs(fd, modname, "", "MOD", modmap, [], msc, 'lib', '.dll')

def msc_library(fd, var, libmap, msc):

    name = var[4:]
    sep = ""
    pref = 'lib'
    dll = '.dll'
    if libmap.has_key("NAME"):
        libname = libmap['NAME'][0]
    else:
        libname = name

    if libmap.has_key('PREFIX'):
        if libmap['PREFIX']:
            pref = libmap['PREFIX'][0]
        else:
            pref = ''
    instlib = 1
    if libmap['SOURCES'][0].endswith('.py.i'):
        # if the first source ends in .py.i, it's a Python module
        dll = '.pyd'
        instlib = 0
    else:
        # if underneath a directory called "python" (up to 3 levels),
        # set DLL suffix to ".pyd" and set instlib to 0
        # if underneath a directory called "php" (also up to 3 levels),
        # set instlib to 0 and pref to 'php_'
        h,t = os.path.split(msc['cwd'])
        if t == 'python' or t == 'php':
            if t == 'python':
                dll = '.pyd'
            else:
                pref = 'php_'
            instlib = 0
        else:
            h,t = os.path.split(h)
            if t == 'python' or os.path.basename(h) == 'python':
                dll = '.pyd'
                instlib = 0
            elif t == 'php' or os.path.basename(h) == 'php':
                instlib = 0
                pref = 'php_'

    if (libname[0] == "_"):
        sep = "_"
        libname = libname[1:]
    if libmap.has_key('SEP'):
        sep = libmap['SEP'][0]

    lib = "lib"
    ld = "LIBDIR"
    if libmap.has_key("DIR"):
        lib = libname
        ld = libmap["DIR"][0] # use first name given
    ld = msc_translate_dir(ld,msc)

    HDRS = []
    hdrs_ext = []
    if libmap.has_key('HEADERS'):
        hdrs_ext = libmap['HEADERS']

    SCRIPTS = []
    scripts_ext = []
    if libmap.has_key('SCRIPTS'):
        scripts_ext = libmap['SCRIPTS']

    v = sep + libname
    makedll = pref + v + dll
    if libmap.has_key('NOINST') or libmap.has_key('NOINST_MSC'):
        if libmap.has_key("LIBS") or libmap.has_key("WINLIBS"):
            print "!WARNING: no sense in having a LIBS section with NOINST"
        makelib = pref + v + '.lib'
    else:
        makelib = makedll
    if libmap.has_key('COND'):
        condname = 'defined(' + ') && defined('.join(libmap['COND']) + ')'
        mkname = (pref + v).replace('.', '_').replace('-', '_')
        fd.write('!IF %s\n' % condname)
        fd.write('C_%s_dll = %s%s%s\n' % (mkname, pref, v, dll))
        fd.write('C_%s_lib = %s%s.lib\n' % (mkname, pref, v))
        fd.write('!ELSE\n')
        fd.write('C_%s_dll =\n' % mkname)
        fd.write('C_%s_lib =\n' % mkname)
        fd.write('!ENDIF\n')
        makelib = '$(C_%s_lib)' % mkname
        makedll = '$(C_%s_dll)' % mkname
    else:
        condname = ''

    if libmap.has_key('NOINST') or libmap.has_key('NOINST_MSC'):
        msc['NLIBS'].append(makelib)
    else:
        msc['LIBS'].append(makelib)
        if instlib:
            i = pref + v + '.lib'
        else:
            i = ''
        if ld != 'LIBDIR':
            msc['INSTALL'][pref + v] = makedll, dll, ld, i, condname
        else:
            msc['INSTALL'][pref + v] = makedll, dll, '$(%sdir)' % lib.replace('-', '_'), i, condname

    if libmap.has_key('MTSAFE'):
        fd.write("CFLAGS=$(CFLAGS) $(thread_safe_flag_spec)\n")

    dlib = []
    if libmap.has_key(libname+ "_DLIBS"):
        dlib = libmap[libname+"_DLIBS"]
    liblist = []
    if libmap.has_key("LIBS"):
        liblist = liblist + libmap["LIBS"]
    if libmap.has_key("WINLIBS"):
        liblist = liblist + libmap["WINLIBS"]
    if liblist:
        msc_additional_libs(fd, libname, sep, "LIB", liblist, dlib, msc, pref, dll)

    for src in libmap['SOURCES']:
        base, ext = split_filename(src)
        #if ext not in automake_ext:
        msc['EXTRA_DIST'].append(src)

    srcs = '%s%s%s_OBJS =' % (pref, sep, libname)
    deps = '%s%s%s_DEPS = $(%s%s%s_OBJS)' % (pref, sep, libname, pref, sep, libname)
    deffile = ''
    for target in libmap['TARGETS']:
        if target == "@LIBOBJS@":
            srcs = srcs + " $(LIBOBJS)"
        else:
            t, ext = split_filename(target)
            if ext == "o":
                srcs = srcs + " " + t + ".obj"
            elif ext == "glue.o":
                srcs = srcs + " " + t + ".glue.obj"
            elif ext == "tab.o":
                srcs = srcs + " " + t + ".tab.obj"
            elif ext == "yy.o":
                srcs = srcs + " " + t + ".yy.obj"
            elif ext == "py.o":
                srcs = srcs + " " + t + ".py.obj"
            elif ext == "pm.o":
                srcs = srcs + " " + t + ".pm.obj"
            elif ext == 'res':
                srcs = srcs + " " + t + ".res"
            elif ext in hdrs_ext:
                HDRS.append(target)
            elif ext in scripts_ext:
                if target not in SCRIPTS:
                    SCRIPTS.append(target)
            elif ext == 'def':
                deffile = ' "-DEF:%s"' % target
                deps = deps + " " + target
    fd.write(srcs + "\n")
    fd.write(deps + "\n")
    ln = pref + sep + libname
    if libmap.has_key('NOINST') or libmap.has_key('NOINST_MSC'):
        ln_ = ln.replace('-','_')
        fd.write("%s.lib: $(%s_DEPS)\n" % (ln, ln_))
        fd.write('\t$(ARCHIVER) /out:"%s.lib" $(%s_OBJS) $(%s_LIBS)\n' % (ln, ln_, ln_))
    else:
        fd.write("%s.lib: %s%s\n" % (ln, ln, dll))
        fd.write("%s%s: $(%s_DEPS) \n" % (ln, dll, ln.replace('-','_')))
        fd.write('\t"$(TOPDIR)\\..\\NT\\wincompile.py" $(CC) $(CFLAGS) -LD -Fe%s%s @<< /link @<<\n$(%s_OBJS)\n<<\n$(%s_LIBS)%s\n<<\n' % (ln, dll, ln.replace('-','_'), ln.replace('-','_'), deffile))
        fd.write("\tif exist $@.manifest $(MT) -manifest $@.manifest -outputresource:$@;2\n");
        if sep == '_':
            fd.write('\tif not exist .libs $(MKDIR) .libs\n')
            fd.write('\t$(INSTALL) "%s%s" ".libs\\%s%s"\n' % (ln, dll, ln, dll))
    fd.write("\n")

    if SCRIPTS:
        fd.write(libname.replace('-','_')+"_SCRIPTS =" + msc_space_sep_list(SCRIPTS))
        msc['BUILT_SOURCES'].append("$(" + name.replace('-','_') + "_SCRIPTS)")

    if libmap.has_key('HEADERS'):
        for h in HDRS:
            msc['HDRS'].append(h)

    msc_deps(fd, libmap['DEPS'], ".obj", msc)

def msc_libs(fd, var, libsmap, msc):

    lib = "lib"
    ld = "LIBDIR"
    if libsmap.has_key("DIR"):
        lib = "libs"
        ld = libsmap["DIR"][0] # use first name given
    ld = msc_translate_dir(ld,msc)

    sep = ""
    if libsmap.has_key('SEP'):
        sep = libsmap['SEP'][0]

    SCRIPTS = []
    scripts_ext = []
    if libsmap.has_key('SCRIPTS'):
        scripts_ext = libsmap['SCRIPTS']

    if libsmap.has_key('MTSAFE'):
        fd.write("CFLAGS=$(CFLAGS) $(thread_safe_flag_spec)\n")

    for libsrc in libsmap['SOURCES']:
        libname, ext = split_filename(libsrc)
        #if ext not in automake_ext:
        msc['EXTRA_DIST'].append(libsrc)
        v = sep + libname
        msc['LIBS'].append('lib' + v + '.dll')
        msc['INSTALL']['lib' + v] = 'lib' + v + '.dll', '.dll', ld, 'lib' + v + '.lib', ''

        dlib = []
        if libsmap.has_key(libname + "_DLIBS"):
            dlib = libsmap[libname+"_DLIBS"]
        if libsmap.has_key(libname + "_LIBS"):
            msc_additional_libs(fd, libname, sep, "LIB", libsmap[libname + "_LIBS"], dlib, msc, 'lib', '.dll')
        else:
            libslist = []
            if libsmap.has_key("LIBS"):
                libslist = libslist + libsmap["LIBS"]
            if libsmap.has_key("WINLIBS"):
                libslist = libslist + libsmap["WINLIBS"]
            if libslist:
                msc_additional_libs(fd, libname, sep, "LIB", libslist, dlib, msc, 'lib', '.dll')

        srcs = "lib%s%s_OBJS =" % (sep, libname)
        deps = "lib%s%s_DEPS = $(lib%s%s_OBJS)" % (sep, libname, sep, libname)
        deffile = ''
        for target in libsmap['TARGETS']:
            t, ext = split_filename(target)
            if t == libname:
                t, ext = split_filename(target)
                if ext == "o":
                    srcs = srcs + " " + t + ".obj"
                elif ext == "glue.o":
                    srcs = srcs + " " + t + ".glue.obj"
                elif ext == "tab.o":
                    srcs = srcs + " " + t + ".tab.obj"
                elif ext == "yy.o":
                    srcs = srcs + " " + t + ".yy.obj"
                elif ext == 'res':
                    srcs = srcs + " " + t + ".res"
                elif ext in scripts_ext:
                    if target not in SCRIPTS:
                        SCRIPTS.append(target)
                elif ext == 'def':
                    deffile = ' "-DEF:%s"' % target
                    deps = deps + " " + target
        fd.write(srcs + "\n")
        fd.write(deps + "\n")
        ln = "lib" + sep + libname
        fd.write(ln + ".lib: " + ln + ".dll\n")
        fd.write(ln + ".dll: $(" + ln.replace('-','_') + "_DEPS)\n")
        fd.write('\t"$(TOPDIR)\\..\\NT\\wincompile.py" $(CC) $(CFLAGS) -LD -Fe%s.dll $(%s_OBJS) /link @<<\n$(%s_LIBS)%s\n<<\n' % (ln, ln.replace('-','_'), ln.replace('-','_'), deffile))
        fd.write("\tif exist $@.manifest $(MT) -manifest $@.manifest -outputresource:$@;2\n");
        if sep == '_':
            fd.write('\tif not exist .libs $(MKDIR) .libs\n')
            fd.write('\t$(INSTALL) "%s.dll" ".libs\\%s.dll"\n' % (ln, ln))
        fd.write("\n")

    if SCRIPTS:
        fd.write("SCRIPTS =" + msc_space_sep_list(SCRIPTS))
        msc['BUILT_SOURCES'].append("$(SCRIPTS)")
        msc['SCRIPTS'].append("$(SCRIPTS)")

    if libsmap.has_key('HEADERS'):
        HDRS = []
        hdrs_ext = libsmap['HEADERS']
        for target in libsmap['DEPS'].keys():
            t, ext = split_filename(target)
            if ext in hdrs_ext:
                msc['HDRS'].append(target)

    msc_deps(fd, libsmap['DEPS'], ".obj", msc)

def msc_includes(fd, var, values, msc):
    incs = "-I$(SRCDIR)"
    for i in values:
        # replace all occurrences of @XXX@ with $(XXX)
        i = re.sub('@([A-Z_]+)@', r'$(\1)', i)
        if i[0] == "-":
            incs = incs + ' "%s"' % i.replace('/', '\\')
        elif i[0] == "$":
            incs = incs + ' %s' % i.replace('/', '\\')
        else:
            incs = incs + ' "-I%s"' % msc_translate_dir(i, msc) \
                   + msc_add_srcdir(i, msc, " -I")
    fd.write("INCLUDES = " + incs + "\n")

def msc_gem(fd, var, gem, msc):
    gemre = re.compile(r'\.files *= *\[ *(.*[^ ]) *\]')
    rd = 'RUBY_DIR'
    if gem.has_key('DIR'):
        rd = gem['DIR'][0]
    rd = msc_translate_dir(rd, msc)
    fd.write('!IF defined(HAVE_RUBYGEM)\n')
    for f in gem['FILES']:
        msc['SCRIPTS'].append(f[:-4])
        srcs = map(lambda x: x.strip('" '),
                   gemre.search(open(os.path.join(msc['cwd'], f)).read()).group(1).split(', '))
        srcs.append(f)
        fd.write('%s: %s\n' % (f[:-4], ' '.join(srcs)))
        fd.write('\tgem build %s\n' % f)
        for src in srcs:
            src = src.replace('/', '\\')
            fd.write('%s: "$(SRCDIR)\\%s"\n' % (src, src))
            if '\\' in src:
                d = src[:src.rfind('\\')]
                fd.write('\tif not exist "%s" $(MKDIR) "%s"\n' % (d, d))
            fd.write('\t$(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (src, src))
        msc['INSTALL'][f] = f, '', '', '', 'defined(HAVE_RUBYGEM)'
        fd.write('install_%s: "%s" "%s"\n' % (f, f[:-4], rd))
        fd.write('\tgem install "%s" --local --install-dir "%s" --force --rdoc\n' % (f[:-4], rd))
        fd.write('"%s":\n' % rd)
        fd.write('\tif not exist "%s" $(MKDIR) "%s"\n' % (rd, rd))
    fd.write('!ELSE\n')
    for f in gem['FILES']:
        fd.write('%s:\n' % f[:-4])
        fd.write('install_%s:\n' % f)
    fd.write('!ENDIF\n')

def msc_python(fd, var, python, msc):
    pyre = re.compile(r'packages *= *\[ *(.*[^ ]) *\]')
    for f in python['FILES']:
        msc['SCRIPTS'].append('target_python_%s' % f)
        srcs = map(lambda x: x.strip('\'" ').replace('.', '\\'),
                   pyre.search(open(os.path.join(msc['cwd'], f)).read()).group(1).split(', '))
        fd.write('target_python_%s: %s %s\n' % (f, ' '.join(srcs), f))
        fd.write('\t$(PYTHON) %s build\n' % f)
        for src in srcs:
            fd.write('%s: "$(SRCDIR)\\%s"\n' % (src, src))
            fd.write('\tif not exist "%s" $(MKDIR) "%s"\n' % (src, src))
            fd.write('\t$(INSTALL) "$(SRCDIR)\\%s"\\*.py "%s"\n' % (src, src))
        fd.write('%s: "$(SRCDIR)\\%s"\n' % (f, f))
        fd.write('\t$(INSTALL) "$(SRCDIR)\\%s" "%s"\n' % (f, f))
        msc['INSTALL'][f] = f, '', '', '', ''
        fd.write('install_%s:\n' % f)
        fd.write('\t$(PYTHON) %s install --prefix "$(prefix)"\n' % f)

callantno = 0
def msc_ant(fd, var, ant, msc):
    global callantno

    target = var[4:]                    # the ant target to call

    jd = "JAVADIR"
    if ant.has_key("DIR"):
        jd = ant["DIR"][0] # use first name given
    jd = msc_translate_dir(jd, msc)

    if ant.has_key("SOURCES"):
        for src in ant['SOURCES']:
            msc['EXTRA_DIST'].append(src)

    if ant.has_key('COND'):
        condname = 'defined(' + ') && defined('.join(ant['COND']) + ')'
        condname = 'defined(HAVE_JAVA) && ' + condname
    else:
        condname = 'defined(HAVE_JAVA)'
    fd.write("\n!IF %s\n\n" % condname) # there is ant if configure set HAVE_JAVA

    # we create a bat file that contains the call to ant so that we
    # can get hold of the full path name of the current working
    # directory
    fd.write("callant%d.bat:\n" % callantno)
    fd.write("\techo @set thisdir=%%~dp0>callant%d.bat\n" % callantno)
    fd.write("\techo @set thisdir=%%thisdir:~0,-1%%>>callant%d.bat\n" % callantno)
    fd.write("\techo @$(ANT) -f $(SRCDIR)\\build.xml \"-Dbuilddir=%%thisdir%%\" \"-Djardir=%%thisdir%%\" %s>>callant%d.bat\n" % (target, callantno))
    fd.write("%s_ant_target: callant%d.bat\n" % (target, callantno))
    fd.write("\tcallant%d.bat\n" % callantno)
    callantno = callantno + 1


    # install is done at the end, here we simply collect to be installed files
    # INSTALL expects a list of dst,src,ext,install_directory,'lib?'.
    for file in ant['FILES']:
        sfile = file.replace(".", "_")
        fd.write('%s: %s_ant_target\n' % (file, target))
        msc['INSTALL'][file] = file, '', jd, '', condname

    fd.write("\n!ELSE\n\n")

    fd.write('%s:\n' % file)
    fd.write('install_%s:\n' % file)
    fd.write("%s_ant_target:\n" % target)

    fd.write("\n!ENDIF #%s\n\n" % condname)

    # make sure the jars and classes get made
    msc['SCRIPTS'].append(target + '_ant_target')

output_funcs = {'SUBDIRS': msc_subdirs,
                'EXTRA_DIST': msc_extra_dist,
                'EXTRA_HEADERS': msc_extra_headers,
                'LIBDIR': msc_libdir,
                'LIBS': msc_libs,
                'LIB': msc_library,
                'BINS': msc_bins,
                'BIN': msc_binary,
                'DOC': msc_doc,
                'SCRIPTS': msc_scripts,
                'INCLUDES': msc_includes,
                'MTSAFE': msc_mtsafe,
                'CFLAGS': msc_cflags,
                'STATIC_MODS': msc_mods_to_libs,
                'smallTOC_SHARED_MODS': msc_mods_to_libs,
                'largeTOC_SHARED_MODS': msc_mods_to_libs,
                'HEADERS': msc_headers,
                'ANT': msc_ant,
                'GEM': msc_gem,
                'PYTHON': msc_python,
                }

def output(tree, cwd, topdir):
    # HACKS to keep uncompilable stuff out of Windows makefiles.
    for k, v in tree.items():
        if type(v) is type({}):
            if v.has_key('COND'):
                if 'NOT_WIN32' in v['COND']:
                    del tree[k]

    fd = open(os.path.join(cwd, 'Makefile.msc'), "w")

    fd.write(MAKEFILE_HEAD)

    if not tree.has_key('INCLUDES'):
        tree.add('INCLUDES', [])

    msc = {}
    msc['BUILT_SOURCES'] = []
    msc['EXTRA_DIST'] = []
    msc['LIBS'] = []            # libraries which are installed (DLLs)
    msc['NLIBS'] = []           # archives (libraries which are not installed)
    msc['SCRIPTS'] = []
    msc['BINS'] = []
    msc['NBINS'] = []
    msc['HDRS'] = []
    msc['INSTALL'] = {}
    msc['LIBDIR'] = 'lib'
    msc['TREE'] = tree
    msc['cwd'] = cwd
    msc['DEPS'] = []
    msc['_IN'] = []

    prefix = os.path.commonprefix([cwd, topdir])
    d = cwd[len(prefix):]
    reldir = os.curdir
    srcdir = d
    if len(d) > 1 and d[0] == os.sep:
        d = d[len(os.sep):]
        while d:
            reldir = os.path.join(reldir, os.pardir)
            d, t = os.path.split(d)

    fd.write("TOPDIR = %s\n" % string.replace(reldir, '/', '\\'))
    fd.write("SRCDIR = $(TOPDIR)\\..%s\n" % string.replace(srcdir, '/', '\\'))
    fd.write("!INCLUDE $(TOPDIR)\\..\\NT\\rules.msc\n")
    if tree.has_key("SUBDIRS"):
        fd.write("all: all-recursive all-msc\n")
        fd.write("check: check-recursive check-msc\n")
        fd.write("install: install-recursive install-msc\n")
    else:
        fd.write("all: all-msc\n")
        fd.write("check: check-msc\n")
        fd.write("install: install-msc\n")

    for i, v in tree.items():
        j = i
        if string.find(i, '_') >= 0:
            k, j = string.split(i, '_', 1)
            j = string.upper(k)
        if type(v) is type([]):
            if output_funcs.has_key(i):
                output_funcs[i](fd, i, v, msc)
            elif output_funcs.has_key(j):
                output_funcs[j](fd, i, v, msc)
            elif i != 'TARGETS':
                msc_assignment(fd, i, v, msc)

    for i, v in tree.items():
        j = i
        if string.find(i, '_') >= 0:
            k, j = string.split(i, '_', 1)
            j = string.upper(k)
        if type(v) is type({}):
            if output_funcs.has_key(i):
                output_funcs[i](fd, i, v, msc)
            elif output_funcs.has_key(j):
                output_funcs[j](fd, i, v, msc)
            elif i != 'TARGETS':
                msc_assignment(fd, i, v, msc)

    if msc['BUILT_SOURCES']:
        fd.write("BUILT_SOURCES = ")
        for v in msc['BUILT_SOURCES']:
            fd.write(" %s" % v)
        fd.write("\n")

##    fd.write("EXTRA_DIST = Makefile.ag Makefile.msc")
##    for v in msc['EXTRA_DIST']:
##        fd.write(" %s" % v)
##    fd.write("\n")

    fd.write("all-msc:")
    if msc['LIBS']:
        for v in msc['LIBS']:
            if v[:1] == '$':
                fd.write(' %s' % v)
            else:
                fd.write(' "%s"' % v)

    if msc['NLIBS']:
        for v in msc['NLIBS']:
            if v[:1] == '$':
                fd.write(' %s' % v)
            else:
                fd.write(' "%s"' % v)

    if msc['NBINS']:
        for x, v, cond in msc['NBINS']:
            if v[:1] == '$':
                fd.write(' %s' % v)
            else:
                fd.write(' "%s.exe"' % v)

    if msc['BINS']:
        for x, v, cond in msc['BINS']:
            if v[:1] == '$':
                fd.write(' %s' % v)
            else:
                fd.write(' "%s.exe"' % v)

    if msc['SCRIPTS']:
        for v in msc['SCRIPTS']:
            if v[:1] == '$':
                fd.write(' %s' % v)
            else:
                fd.write(' "%s"' % v)

    if cwd != topdir and msc['HDRS']:
        for v in msc['HDRS']:
            if v[:1] == '$':
                fd.write(' %s' % v)
            else:
                fd.write(' "%s"' % v)

    fd.write("\n")

    fd.write("check-msc: all-msc")
    if msc['INSTALL']:
        for dst, (src, ext, dir, instlib, cond) in msc['INSTALL'].items():
            if src[:1] == '$':
                fd.write(' %s' % src)
            else:
                fd.write(' "%s"' % src)
    fd.write("\n")

    fd.write("install-msc: install-exec install-data\n")
    l = []
    for dst, (src, ext, dir, instlib, cond) in msc['INSTALL'].items():
        l.append(dst)
    b = []
    for dst, src, cond in msc['BINS']:
        b.append(dst)

    fd.write("install-exec: %s %s\n" % (
        msc_list2string(b, '"install_bin_','" '),
        msc_list2string(l, '"install_','" ')))
    if msc['BINS']:
        for dst, src, cond in msc['BINS']:
            if cond:
                fd.write('!IF %s\n' % cond)
            if src[:1] != '$':
                src = '"%s.exe"' % src
            fd.write('install_bin_%s: %s\n' % (dst, src))
            fd.write('\tif not exist "$(%sdir)" $(MKDIR) "$(%sdir)"\n' % (dst.replace('-','_'), dst.replace('-','_')))
            fd.write('\t$(INSTALL) %s "$(%sdir)"\n' % (src,dst.replace('-','_')))
            if cond:
                fd.write('!ELSE\n')
                fd.write('install_bin_%s:\n' % dst)
                fd.write('!ENDIF\n')
    if msc['INSTALL']:
        for dst, (src, ext, dir, instlib, cond) in msc['INSTALL'].items():
            if not dir:
                continue
            if cond:
                fd.write('!IF %s\n' % cond)
            fd.write('install_%s: "%s" "%s"\n' % (dst, src, dir))
            fd.write('\t$(INSTALL) "%s" "%s\\%s%s"\n' % (src, dir, dst, ext))
            if instlib:
                fd.write('\t$(INSTALL) "%s" "%s\\%s%s"\n' % (instlib, dir, dst, '.lib'))
            if cond:
                fd.write('!ELSE\n')
                fd.write('install_%s:\n' % dst)
                fd.write('!ENDIF\n')
        td = {}
        for dst, (src, ext, dir, instlib, cond) in msc['INSTALL'].items():
            if not dir:
                continue
            if not td.has_key(dir):
                fd.write('"%s":\n' % dir)
                fd.write('\tif not exist "%s" $(MKDIR) "%s"\n' % (dir, dir))
                td[dir] = 1

    fd.write("install-data:")
    if cwd != topdir and msc['HDRS']:
        name=os.path.split(cwd)[1]
        if name:
            tHDRS = []
            for h in msc['HDRS']:
                tHDRS.append(msc_translate_dir(msc_translate_file(h, msc), msc))
            fd.write(" install-%sinclude_HEADERS\n" % name)
            fd.write("%sincludedir = $(includedir)\\%s\n" % (name.replace('-','_'), name))
            fd.write("%sinclude_HEADERS = %s\n" % (name.replace('-','_'), msc_list2string(tHDRS, " ", "")))
            fd.write("install-%sinclude_HEADERS: $(%sinclude_HEADERS)\n" % (name,name.replace('-','_')))
            fd.write('\tif not exist "$(%sincludedir)" $(MKDIR) "$(%sincludedir)"\n' % (name.replace('-','_'),name.replace('-','_')))
            for h in tHDRS:
                fd.write('\t$(INSTALL) "%s" "$(%sincludedir)"\n' % (h,name.replace('-','_')))
    fd.write("\n")
