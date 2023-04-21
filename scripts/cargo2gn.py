#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import print_function

import os
import os.path
import sys
import argparse
import glob
import json
import re
import shutil

# Rust path
RUST_PATH = '//third_party/rust/'

# import content added to all generated BUILD.gn files. 
IMPORT_CONTENT = '//build/templates/rust/ohos.gni'

# The name of the temporary output directory.
TARGET_TEMP = 'target_temp'

# Header added to all generated BUILD.gn files.
BUILD_GN_HEADER = (
    '# Copyright (c) 2023 Huawei Device Co., Ltd.\n' +
    '# Licensed under the Apache License, Version 2.0 (the "License");\n' +
    '# you may not use this file except in compliance with the License.\n' +
    '# You may obtain a copy of the License at\n' +
    '#\n' +
    '#     http://www.apache.org/licenses/LICENSE-2.0\n' +
    '#\n' +
    '# Unless required by applicable law or agreed to in writing, software\n' +
    '# distributed under the License is distributed on an "AS IS" BASIS,\n' +
    '# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n' +
    '# See the License for the specific language governing permissions and\n' +
    '# limitations under the License.\n')

# Message to be displayed when this script is called without the --run flag.
DRY_RUN_CONTENT = (
    'Dry-run: This script uses ./' + TARGET_TEMP + ' for output directory,\n' +
    'runs cargo clean, runs cargo build -v, saves output to ./cargo.out,\n' +
    'and writes to BUILD.gn in the current and subdirectories.\n\n' +
    'To do do all of the above, use the --run flag.\n' +
    'See --help for other flags, and more usage notes in this script.\n')

# Rust package name with suffix -d1.d2.d3(+.*)?.
VERSION_SUFFIX_RE = re.compile(r'^(.*)-[0-9]+\.[0-9]+\.[0-9]+(?:\+.*)?$')

# Crate types corresponding to a library
LIBRARY_CRATE_TYPES = ['staticlib', 'cdylib', 'lib', 'rlib', 'dylib', 'proc-macro']


def escape_quotes(s):
    # replace '"' with '\\"'
    return s.replace('"', '\\"')


def file_base_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def pkg_to_crate_name(s):
    return s.replace('-', '_').replace('.', '_')


def get_base_name(path):
    return pkg_to_crate_name(file_base_name(path))


def get_crate_name(crate):
    # to sort crates in a list
    return crate.crate_name


def get_designated_pkg_info(lines, designated):
    package = re.compile(r'^ *\[package\]')
    designated_re = re.compile('^ *' + designated + ' *= * "([^"]*)')
    is_package = False
    for line in lines:
        if is_package:
            if designated_re.match(line):
                line = eval(repr(line).replace(f'\\"', ''))
                return designated_re.match(line).group(1)
        else:
            is_package = package.match(line) is not None
    return ''


def is_build_script(name):
    # Judge whether it is build script.
    return name.startswith('build_script_')


def is_dependent_path(path):
    # Absolute('/') or dependent('.../') paths are not main files of this crate.
    return path.startswith('/') or path.startswith('.../')


def unquote(s):
    # remove quotes around str
    if s and len(s) > 1 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def remove_version_suffix(s):
    # remove -d1.d2.d3 suffix
    if VERSION_SUFFIX_RE.match(s):
        return VERSION_SUFFIX_RE.match(s).group(1)
    return s


def short_out_name(pkg, s):
    # replace /.../pkg-*/out/* with .../out/*
    return re.sub('^/.*/' + pkg + '-[0-9a-f]*/out/', '.../out/', s)


class Crate(object):
    """Information of a Rust crate to collect/emit for an BUILD.gn module."""

    def __init__(self, runner, outfile_name):
        # Remembered global runner
        self.runner = runner
        self.debug = runner.args.debug
        self.cargo_dir = ''              # directory of my Cargo.toml
        self.outfile = None              # open file handle of outfile_name during dump*
        self.outfile_name = outfile_name # path to BUILD.gn
        # GN module properties derived from rustc parameters.
        self.module_type = ''            # lib,crate_name,test etc.
        self.root_pkg_name = ''          # parent package name of a sub/test packge
        # Save parsed status
        self.error_infos = ''            # all errors found during parsing
        self.line = ''                   # original rustc command line parameters
        self.line_num = 1                # runner told input source line number
        # Parameters collected from rustc command line.
        self.cap_lints = ''
        self.crate_name = ''
        self.edition = '2015'            # cargo default is 2015, you can specify the edition as 2018 or 2021
        self.emit_list = ''              # --emit=dep-info,metadata,link
        self.main_src = ''
        self.target = ''
        self.cfgs = list()
        self.core_deps = list()          # first part of self.deps elements
        self.crate_types = list()
        self.deps = list()
        self.features = list()
        self.ignore_options = list()
        self.srcs = list()               # main_src or merged multiple source files
        self.shared_libs = list()        # -l dylib=wayland-client, -l z
        self.static_libs = list()        # -l static=host_cpuid
        # Parameters collected from Cargo.toml.
        self.cargo_pkg_version = ''      # value extracted from Cargo.toml version field
        self.cargo_pkg_authors = ''      # value extracted from Cargo.toml authors field
        self.cargo_pkg_name = ''         # value extracted from Cargo.toml name field
        self.cargo_pkg_description = ''  # value extracted from Cargo.toml description field
        # Parameters related to build.rs.
        self.build_root = ''
        self.checked_out_files = False   # to check only once
        self.build_script_outputs = []   # output files generated by build.rs

    def write(self, s):
        # convenient way to output one line at a time with EOL.
        self.outfile.write(s + '\n')

    def parse_rustc(self, line_num, line):
        """Find important rustc arguments to convert to BUILD.gn properties."""
        self.line_num = line_num
        self.line = line
        args = line.split()  # Loop through every argument of rustc.
        self.parse_args(args)
        if not self.crate_name:
            self.error_infos += 'ERROR: missing --crate-name\n'
        if not self.crate_types:
            if 'test' in self.cfgs:
                self.crate_types.append('test')
            else:
                self.error_infos += 'ERROR: missing --crate-type or --test\n'
        elif len(self.crate_types) > 1:
            if 'lib' in self.crate_types and 'rlib' in self.crate_types:
                self.error_infos += 'ERROR: cannot generate both lib and rlib crate types\n'
            if 'test' in self.crate_types:
                self.error_infos += 'ERROR: cannot handle both --crate-type and --test\n'
        if not self.main_src:
            self.error_infos += 'ERROR: missing main source file\n'
        else:
            self.srcs.append(self.main_src)
        if self.cargo_dir:
            self.get_root_pkg_name()
        if not self.root_pkg_name:
            self.root_pkg_name = self.crate_name

        # Process crate with build.rs
        if not self.skip_crate():
            if not self.runner.args.no_pkg_info:
                self.find_pkg_info()
            self.find_build_root()
            if self.runner.args.copy_out:
                self.copy_out_files()
            elif self.find_out_files() and self.has_used_out_dir():
                self.copy_out_files()

        self.cfgs = sorted(set(self.cfgs))
        self.core_deps = sorted(set(self.core_deps))
        self.crate_types = sorted(set(self.crate_types))
        self.deps = sorted(set(self.deps))
        self.features = sorted(set(self.features))
        self.ignore_options = sorted(set(self.ignore_options))
        self.static_libs = sorted(set(self.static_libs))
        self.shared_libs = sorted(set(self.shared_libs))
        self.decide_module_type()
        return self

    def parse_args(self, args):
        num = 0
        while num < len(args):
            arg = args[num]
            if arg == '--crate-name':
                num += 1
                self.crate_name = args[num]
            elif arg == '--crate-type':
                num += 1
                self.crate_types.append(args[num])
            elif arg == '--cfg':
                num += 1
                self.deal_cfg(args[num])
            elif arg == '-C':
                num += 1
                self.add_ignore_options_flag(args[num])  # codegen options
            elif arg.startswith('-C'):
                self.add_ignore_options_flag(arg[2:])
            elif arg == '--cap-lints':
                num += 1
                self.cap_lints = args[num]
            elif arg.startswith('--edition='):
                self.edition = arg.replace('--edition=', '')
            elif arg.startswith('--emit='):
                self.emit_list = arg.replace('--emit=', '')
            elif arg == '--extern':
                num += 1
                self.deal_extern(args[num])
            elif (arg.startswith('--error-format=') or arg.startswith('--json=') or
                  arg.startswith('\'-Aclippy')):
                _ = arg  # ignored
            elif arg == '-L':
                num += 1
                self.set_root_pkg_name(args[num])
            elif arg == '-l':
                num += 1
                self.deal_static_and_dylib(args[num])
            elif arg == '--out-dir' or arg == '--color':  # ignored
                num += 1
            elif arg == '--target':
                num += 1
                self.target = args[num]
            elif arg == '--test':
                self.crate_types.append('test')
            elif not arg.startswith('-'):
                self.set_main_src(args[num])
            else:
                self.error_infos += 'ERROR: unknown ' + arg + '\n'
            num += 1

    def deal_cfg(self, arg):
        if arg.startswith('\'feature='):
            feature = unquote(arg.replace('\'feature=', '')[:-1])
            # 'runtime' feature removed because it conflicts with static
            if feature == 'runtime':
                feature = 'static'
            self.features.append(feature)
        else:
            self.cfgs.append(arg)

    def add_ignore_options_flag(self, flag):
        """Ignore options not used in GN."""
        # 'codegen-units' is set in GN global config or by default
        # 'embed-bitcode' is ignored; we might control LTO with other .gn flag
        # 'prefer-dynamic' does not work with common flag -C lto
        if not (flag.startswith('codegen-units=') or flag.startswith('debuginfo=') or
                flag.startswith('embed-bitcode=') or flag.startswith('extra-filename=') or
                flag.startswith('incremental=') or flag.startswith('metadata=') or
                flag == 'prefer-dynamic'):
            self.ignore_options.append(flag)

    def deal_extern(self, arg):
        deps = re.sub('=/[^ ]*/deps/', ' = ', arg)
        self.deps.append(deps)
        self.core_deps.append(re.sub(' = .*', '', deps))

    def set_root_pkg_name(self, arg):
        if arg.startswith('dependency=') and arg.endswith('/deps'):
            if '/' + TARGET_TEMP + '/' in arg:
                self.root_pkg_name = re.sub('^.*/', '',
                                            re.sub('/' + TARGET_TEMP + '/.*/deps$', '', arg))
            else:
                self.root_pkg_name = re.sub('^.*/', '',
                                            re.sub('/[^/]+/[^/]+/deps$', '', arg))
            self.root_pkg_name = remove_version_suffix(self.root_pkg_name)

    def deal_static_and_dylib(self, arg):
        if arg.startswith('static='):
            self.static_libs.append(re.sub('static=', '', arg))
        elif arg.startswith('dylib='):
            self.shared_libs.append(re.sub('dylib=', '', arg))
        else:
            self.shared_libs.append(arg)

    def set_main_src(self, arg):
        self.main_src = re.sub(r'^/[^ ]*/registry/src/', '.../', arg)
        self.main_src = re.sub(r'^\.\.\./github.com-[0-9a-f]*/', '.../', self.main_src)
        self.find_cargo_dir()
        if self.cargo_dir:
            if self.runner.args.no_subdir:
                # all .gn content to /dev/null
                self.outfile_name = '/dev/null'
            elif not self.runner.args.one_file:
                # Use Cargo.toml to write BUILD.gn in the subdirectory.
                self.outfile_name = os.path.join(self.cargo_dir, 'BUILD.gn')
                self.main_src = self.main_src[len(self.cargo_dir) + 1:]

    def find_cargo_dir(self):
        """Deepest directory with Cargo.toml and contains the main_src."""
        if not is_dependent_path(self.main_src):
            dir_name = os.path.dirname(self.main_src)
            while dir_name:
                if dir_name.endswith('.'):
                    dir_name = os.path.dirname(dir_name)
                    continue
                if os.path.exists(os.path.join(dir_name, 'Cargo.toml')):
                    self.cargo_dir = dir_name
                    return
                dir_name = os.path.dirname(dir_name)

    def skip_crate(self):
        """Return crate_name or a message if this crate should be skipped."""
        # Some Rust packages include extra unwanted crates.
        # This set contains all such excluded crate names.
        excluded_crates = set(['protobuf_bin_gen_rust_do_not_use'])
        if (is_build_script(self.crate_name) or
                self.crate_name in excluded_crates):
            return self.crate_name
        if is_dependent_path(self.main_src):
            return 'dependent crate'
        return ''

    def get_root_pkg_name(self):
        """Read name of [package] in ./Cargo.toml."""
        cargo_toml_path = './Cargo.toml'
        if self.cargo_dir:
            cargo_toml_path = os.path.join(
                os.path.join('.', self.cargo_dir), 'Cargo.toml')
        if not os.path.exists(cargo_toml_path):
            return
        with open(cargo_toml_path, 'r') as infile:
            self.root_pkg_name = get_designated_pkg_info(infile, 'name')
        return

    def find_pkg_info(self):
        """Read package info of [package] in ./Cargo.toml."""
        cargo_toml_path = './Cargo.toml'
        if self.cargo_dir:
            cargo_toml_path = os.path.join(
                os.path.join('.', self.cargo_dir), 'Cargo.toml')
        if not os.path.exists(cargo_toml_path):
            return
        with open(cargo_toml_path, 'r') as infile:
            if self.root_pkg_name:
                self.cargo_pkg_name = self.root_pkg_name
            else:
                self.cargo_pkg_name = get_designated_pkg_info(infile, 'name')
            infile.seek(0)
            self.cargo_pkg_version = get_designated_pkg_info(infile, 'version')
            infile.seek(0)
            pkg_description = get_designated_pkg_info(infile, 'description')
            pkg_description = pkg_description.replace('\n', '').replace(r'\n', '').strip()
            self.cargo_pkg_description = pkg_description
            infile.seek(0)
            authors_re = re.compile(' *authors *= * \[(.*?)\]', re.S)
            authors_section = authors_re.search(infile.read())
            if authors_section:
                authors = authors_section.group(1)
                authors = authors.replace('\n', '').replace('  ', ' ').replace('"', '').strip()
                if authors.endswith(','):
                    authors = authors[:-1]
                self.cargo_pkg_authors = authors

    def find_build_root(self):
        """Read build of [package] in ./Cargo.toml."""
        cargo_toml_path = './Cargo.toml'
        if self.cargo_dir:
            cargo_toml_path = os.path.join(
                os.path.join('.', self.cargo_dir), 'Cargo.toml')
        if not os.path.exists(cargo_toml_path):
            return
        with open(cargo_toml_path, 'r') as infile:
            self.build_root = get_designated_pkg_info(infile, 'build')
        if not self.build_root:
            build_rs_path = './build.rs'
            if self.cargo_dir:
                build_rs_path = os.path.join(os.path.join('.', self.cargo_dir), 'build.rs')
            if os.path.exists(build_rs_path):
                self.build_root = 'build.rs'

    def find_out_files(self):
        # normal_output_list has build.rs output for normal crates
        normal_output_list = glob.glob(
            TARGET_TEMP + '/*/*/build/' + self.root_pkg_name + '-*/out/*')
        # other_output_list has build.rs output for proc-macro crates
        other_output_list = glob.glob(
            TARGET_TEMP + '/*/build/' + self.root_pkg_name + '-*/out/*')
        return normal_output_list + other_output_list

    def has_used_out_dir(self):
        """Returns true if env!("OUT_DIR") is found."""
        cmd = 'grep -rl --exclude build.rs --include \\*.rs \'env!("OUT_DIR")\' * > /dev/null'
        if self.cargo_dir:
            cmd = 'grep -rl --exclude '
            cmd += os.path.join(self.cargo_dir, 'build.rs')
            cmd += ' --include \\*.rs \'env!("OUT_DIR")\' * > /dev/null'
        return 0 == os.system(cmd)

    def copy_out_files(self):
        """Copy build.rs output files to ./out and set up build_script_outputs."""
        if self.checked_out_files:
            return
        self.checked_out_files = True
        cargo_out_files = self.find_out_files()
        out_files = set()
        out_path = 'out'
        if self.cargo_dir:
            out_path = os.path.join(self.cargo_dir, out_path)
        if cargo_out_files:
            os.makedirs(out_path, exist_ok=True)
        for path in cargo_out_files:
            file_name = path.split('/')[-1]
            out_files.add(file_name)
        self.build_script_outputs = sorted(out_files)

    def decide_module_type(self):
        # Use the first crate type for the default/first module.
        crate_type = self.crate_types[0] if self.crate_types else ''
        self.decide_one_module_type(crate_type)

    def decide_one_module_type(self, crate_type):
        """Decide which GN module type to use."""
        if crate_type == 'bin':
            self.module_type = self.crate_name
        elif crate_type in LIBRARY_CRATE_TYPES:
            self.module_type = 'lib'
        elif crate_type == 'test':
            self.module_type = 'test'
        else:
            self.module_type = ''

    def merge_crate(self, other, outfile_name):
        """Try to merge crate into self."""
        # Cargo build --tests could recompile a library for tests.
        # We need to merge such duplicated calls to rustc, with the
        # algorithm in is_should_merge.
        should_merge = self.is_should_merge(other)
        should_merge_test = False
        if not should_merge:
            should_merge_test = self.merge_test(other)
        if should_merge or should_merge_test:
            self.runner.init_gn_file(outfile_name)
            # to write debug info
            with open(outfile_name, 'a') as outfile:
                self.outfile = outfile
                other.outfile = outfile
                self.execute_merge(other, should_merge_test)
            return True
        return False

    def is_should_merge(self, other):
        return (self.crate_name == other.crate_name and
                self.crate_types == other.crate_types and
                self.main_src == other.main_src and
                self.root_pkg_name == other.root_pkg_name and
                not self.skip_crate() and self.is_same_flags(other))

    def merge_test(self, other):
        """Returns true if self and other are tests of same root_pkg_name."""
        # Before merger, each test has its own crate_name. A merged test uses
        # its source file base name as output file name, so a test is mergeable
        # only if its base name equals to its crate name.
        return (self.crate_types == other.crate_types and self.crate_types == ['test'] and
                self.root_pkg_name == other.root_pkg_name and not self.skip_crate() and
                other.crate_name == get_base_name(other.main_src) and
                (len(self.srcs) > 1 or (self.crate_name == get_base_name(self.main_src))) and
                self.is_same_flags(other))

    def is_same_flags(self, other):
        return (not self.error_infos and not other.error_infos and
                self.cap_lints == other.cap_lints and self.cfgs == other.cfgs and
                self.core_deps == other.core_deps and self.edition == other.edition and
                self.emit_list == other.emit_list and self.features == other.features and
                self.ignore_options == other.ignore_options and
                self.static_libs == other.static_libs and
                self.shared_libs == other.shared_libs)

    def execute_merge(self, other, should_merge_test):
        """Merge attributes of other to self."""
        if self.debug:
            self.write('\n// Before merge definition(self):')
            self.dump_debug_info()
            self.write('\n// Before merge definition(other):')
            other.dump_debug_info()
        if not self.target:
            # okay to keep only the first target triple
            self.target = other.target
        self.decide_module_type()
        if should_merge_test:
            if (self.runner.should_ignore_test(self.main_src) and
                not self.runner.should_ignore_test(other.main_src)):
                self.main_src = other.main_src
            self.srcs.append(other.main_src)
            self.crate_name = pkg_to_crate_name(self.root_pkg_name)
        if self.debug:
            self.write('\n// After merge definition:')
            self.dump_debug_info()

    def dump(self):
        """Dump all error/debug/module code to the output .gn file."""
        self.runner.init_gn_file(self.outfile_name)
        with open(self.outfile_name, 'a') as outfile:
            self.outfile = outfile
            if self.error_infos:
                self.dump_line()
                self.write(self.error_infos)
            elif self.skip_crate():
                self.dump_skip_crate(self.skip_crate())
            else:
                if self.debug:
                    self.dump_debug_info()
                self.dump_gn_module()

    def dump_debug_info(self):
        """Dump parsed data, when cargo2gn is called with --debug."""

        def dump(name, value):
            self.write('//%12s = %s' % (name, value))

        def dump_list(fmt, values):
            for v in values:
                self.write(fmt % v)

        def opt_dump(name, value):
            if value:
                dump(name, value)

        self.dump_line()
        dump('crate_name', self.crate_name)
        dump('crate_types', self.crate_types)
        opt_dump('edition', self.edition)
        opt_dump('emit_list', self.emit_list)
        dump('main_src', self.main_src)
        dump('module_type', self.module_type)
        opt_dump('target', self.target)
        opt_dump('cap_lints', self.cap_lints)
        dump_list('// cfg = %s', self.cfgs)
        dump_list('// cfg = \'feature "%s"\'', self.features)
        dump_list('// codegen = %s', self.ignore_options)
        dump_list('// deps = %s', self.deps)
        dump_list('// -l (dylib) = %s', self.shared_libs)
        dump_list('// -l static = %s', self.static_libs)

    def dump_line(self):
        self.write('\n// Line ' + str(self.line_num) + ' ' + self.line)

    def dump_skip_crate(self, kind):
        if self.debug:
            self.write('\n// IGNORED: ' + kind + ' ' + self.main_src)
        return self

    def dump_gn_module(self):
        """Dump one or more GN module definition, depending on crate_types."""
        if len(self.crate_types) == 1:
            self.dump_single_type_gn_module()
            return
        if 'test' in self.crate_types:
            self.write('\nERROR: multiple crate types cannot include test type')
            return
        # Dump one GN module per crate_type.
        for crate_type in self.crate_types:
            self.decide_one_module_type(crate_type)
            self.dump_one_gn_module(crate_type)

    def dump_single_type_gn_module(self):
        """Dump one simple GN module, which has only one crate_type."""
        crate_type = self.crate_types[0]
        if crate_type != 'test':
            self.dump_one_gn_module(crate_type)
            return
        # Dump one test module per source file.
        self.srcs = [
            src for src in self.srcs if not self.runner.should_ignore_test(src)]
        if len(self.srcs) > 1:
            self.srcs = sorted(set(self.srcs))
        saved_srcs = self.srcs
        for src in saved_srcs:
            self.srcs = [src]
            saved_main_src = self.main_src
            self.main_src = src
            self.decide_one_module_type(crate_type)
            self.dump_one_gn_module(crate_type)
            self.main_src = saved_main_src
        self.srcs = saved_srcs

    def dump_one_gn_module(self, crate_type):
        """Dump one GN module definition."""
        if not self.module_type:
            self.write('\nERROR: unknown crate_type ' + crate_type)
            return
        self.write('\nohos_cargo_crate("' + self.module_type + '") {')
        self.dump_gn_first_properties(crate_type)
        self.dump_gn_core_properties()
        self.write('}')

    def dump_gn_first_properties(self, crate_type):
        if crate_type != 'bin':
            self.write('    crate_name = "' + self.crate_name + '"')
        if crate_type:
            if crate_type == 'lib':
                crate_type = 'rlib'
            self.write('    crate_type = "' + crate_type + '"')
        if self.main_src:
            self.write('    crate_root = "' + self.main_src + '"')
        if self.crate_name.startswith('lib'):
            self.write('    output_name = "lib' + self.crate_name + '"')
        self.write('')

    def dump_gn_core_properties(self):
        self.dump_sources_list()
        if self.edition:
            self.write('    edition = "' + self.edition + '"')
        if not self.runner.args.no_pkg_info:
            if self.cargo_pkg_version:
                self.write('    cargo_pkg_version = "' +
                           self.cargo_pkg_version + '"')
            if self.cargo_pkg_authors:
                self.write('    cargo_pkg_authors = "' +
                           self.cargo_pkg_authors + '"')
            if self.cargo_pkg_name:
                self.write('    cargo_pkg_name = "' +
                           self.cargo_pkg_name + '"')
            if self.cargo_pkg_description:
                self.write('    cargo_pkg_description = "' +
                           self.cargo_pkg_description + '"')
        if self.deps:
            self.dump_gn_deps()
        if self.build_root and self.root_pkg_name in self.runner.build_deps:
            self.dump_gn_build_deps()
        self.dump_gn_property_list('features', '"%s"', self.features)
        if self.build_root:
            self.write('    build_root = "' + self.build_root + '"')
            build_sources = list()
            build_sources.append(self.build_root)
            self.dump_gn_property_list('build_sources', '"%s"', build_sources)
            if self.build_script_outputs:
                self.dump_gn_property_list(
                    'build_script_outputs', '"%s"', self.build_script_outputs)

    def dump_sources_list(self):
        """Dump the srcs list, for defaults or regular modules."""
        if len(self.srcs) > 1:
            srcs = sorted(set(self.srcs))  # make a copy and dedup
            for num in range(len(self.srcs)):
                srcs[num] = srcs[num]
        else:
            srcs = [self.main_src]
        self.dump_gn_property_list('sources', '"%s"', srcs)

    def dump_gn_deps(self):
        """Dump the deps."""
        rust_deps = list()
        deps_libname = re.compile('^.* = lib(.*)-[0-9a-f]*.(rlib|so|rmeta)$')
        for lib in self.deps:
            libname_groups = deps_libname.match(lib)
            if libname_groups is not None:
                lib_name = libname_groups.group(1)
            else:
                lib_name = re.sub(' .*$', '', lib)
            if lib_name in self.runner.args.dependency_blocklist:
                continue
            if lib.endswith('.rlib') or lib.endswith('.rmeta') or lib.endswith('.so'):
                # On MacOS .rmeta is used when Linux uses .rlib or .rmeta.
                rust_lib = self.get_rust_lib(lib_name)
                if rust_lib:
                    rust_lib += ':lib'
                    rust_deps.append(rust_lib)
            elif lib != 'proc_macro':
                # --extern proc_macro is special and ignored
                rust_deps.append('// unknown type of lib: '.join(lib))
        if rust_deps:
            self.dump_gn_property_list('deps', '"%s"', rust_deps)

    def dump_gn_build_deps(self):
        """Dump the build deps."""
        rust_build_deps = list()
        build_deps_libname = re.compile('^.* = lib(.*)-[0-9a-f]*.(rlib|so|rmeta)$')
        build_deps = self.runner.build_deps.get(self.root_pkg_name)
        if not build_deps:
            return
        for lib in build_deps:
            libname_groups = build_deps_libname.match(lib)
            if libname_groups is not None:
                lib_name = libname_groups.group(1)
            else:
                lib_name = re.sub(' .*$', '', lib)
            if lib_name in self.runner.args.dependency_blocklist:
                continue
            if lib.endswith('.rlib') or lib.endswith('.rmeta') or lib.endswith('.so'):
                # On MacOS .rmeta is used when Linux uses .rlib or .rmeta.
                rust_lib = self.get_rust_lib(lib_name)
                if rust_lib:
                    rust_build_deps.append(rust_lib + ':lib')
            elif lib != 'proc_macro':
                # --extern proc_macro is special and ignored
                rust_build_deps.append('// unknown type of lib: '.join(lib))
        if rust_build_deps:
            self.dump_gn_property_list('build_deps', '"%s"', rust_build_deps)

    def dump_gn_property_list(self, name, fmt, values):
        if not values:
            return
        if len(values) > 1:
            self.write('    ' + name + ' = [')
            self.dump_gn_property_list_items(fmt, values)
            self.write('    ]')
        else:
            self.write('    ' + name + ' = [' +
                       (fmt % escape_quotes(values[0])) + ']')

    def dump_gn_property_list_items(self, fmt, values):
        for v in values:
            # fmt has quotes, so we need escape_quotes(v)
            self.write('        ' + (fmt % escape_quotes(v)) + ',')

    def get_rust_lib(self, lib_name):
        rust_lib = ''
        if lib_name:
            crate_name = pkg_to_crate_name(lib_name)
            deps_libname = self.runner.deps_libname_map.get(crate_name)
            if deps_libname:
                rust_lib = RUST_PATH + deps_libname
        return rust_lib


class Runner(object):
    """Main class to parse cargo -v output"""

    def __init__(self, args):
        self.gn_files = set()    # Remember all output BUILD.gn files.
        self.root_pkg_name = ''  # name of package in ./Cargo.toml
        self.args = args
        self.dry_run = not args.run
        self.skip_cargo = args.skipcargo
        self.cargo_path = './cargo'  # path to cargo
        self.crates = list()         # all crates
        self.error_infos = ''        # all error infos
        self.test_error_infos = ''   # all test error infos
        self.warning_files = set()   # all warning files
        self.set_cargo_path()
        # Default operation is cargo clean, followed by build or user given operation.
        if args.cargo:
            self.cargo = ['clean'] + args.cargo
        else:
            # Use the same target for both host and default device builds.
            self.cargo = ['clean', 'build --target x86_64-unknown-linux-gnu']
        self.empty_tests = set()
        self.empty_unittests = False
        self.build_deps = {}
        self.deps_libname_map = {}

    def set_cargo_path(self):
        """Find cargo in the --cargo_bin and set cargo path"""
        if self.args.cargo_bin:
            self.cargo_path = os.path.join(self.args.cargo_bin, 'cargo')
            if os.path.isfile(self.cargo_path):
                print('INFO: using cargo in ' + self.args.cargo_bin)
                return
            else:
                sys.exit('ERROR: cannot find cargo in ' + self.args.cargo_bin)
        else:
            sys.exit('ERROR: the prebuilt cargo is not available; please use the --cargo_bin flag.')
        return

    def run_cargo(self):
        """Run cargo -v and save its output to ./cargo.out."""
        if self.skip_cargo:
            return self
        cargo_toml = './Cargo.toml'
        cargo_out = './cargo.out'
        if not os.access(cargo_toml, os.R_OK):
            print('ERROR: Cannot find ', cargo_toml)
            return self
        cargo_lock = './Cargo.lock'
        cargo_lock_save = './cargo.lock.save'
        have_cargo_lock = os.path.exists(cargo_lock)
        if not self.dry_run:
            if os.path.exists(cargo_out):
                os.remove(cargo_out)
            if not self.args.use_cargo_lock and have_cargo_lock:
                os.rename(cargo_lock, cargo_lock_save)
        # set up search PATH for cargo to find the correct rustc
        save_path = os.environ['PATH']
        os.environ['PATH'] = os.path.dirname(self.cargo_path) + ':' + save_path
        # Add [workspace] to Cargo.toml if it is non-existent.
        is_add_workspace = False
        if self.args.add_workspace:
            with open(cargo_toml, 'r') as in_file:
                cargo_toml_lines = in_file.readlines()
            if '[workspace]\n' in cargo_toml_lines:
                print('WARNING: found [workspace] in Cargo.toml')
            else:
                with open(cargo_toml, 'w') as out_file:
                    out_file.write('[workspace]\n')
                    is_add_workspace = True
        self.deal_cargo_cmd(cargo_out)
        # restore original Cargo.toml
        if is_add_workspace:
            with open(cargo_toml, 'w') as out_file:
                out_file.writelines(cargo_toml_lines)
        if not self.dry_run:
            if not have_cargo_lock:  # restore to no Cargo.lock state
                if os.path.exists(cargo_lock):
                    os.remove(cargo_lock)
            elif not self.args.use_cargo_lock:  # restore saved Cargo.lock
                os.rename(cargo_lock_save, cargo_lock)
        os.environ['PATH'] = save_path
        return self

    def deal_cargo_cmd(self, cargo_out):
        cargo_cmd_v_flag = ' -vv ' if self.args.vv else ' -v '
        cargo_cmd_target_dir = ' --target-dir ' + TARGET_TEMP
        cargo_cmd_redir = ' >> ' + cargo_out + ' 2>&1'
        for cargo in self.cargo:
            cargo_cmd = self.cargo_path + cargo_cmd_v_flag
            features = ''
            if cargo != 'clean':
                if self.args.features is not None:
                    features = ' --no-default-features'
                if self.args.features:
                    features += ' --features ' + self.args.features
            cargo_cmd += cargo + features + cargo_cmd_target_dir + cargo_cmd_redir
            if self.args.rustflags and cargo != 'clean':
                cargo_cmd = 'RUSTFLAGS="' + self.args.rustflags + '" ' + cargo_cmd
            self.run_cargo_cmd(cargo_cmd, cargo_out)

    def run_cargo_cmd(self, cargo_cmd, cargo_out):
        if self.dry_run:
            print('Dry-run skip:', cargo_cmd)
        else:
            with open(cargo_out, 'a') as file:
                file.write('### Running: ' + cargo_cmd + '\n')
            ret = os.system(cargo_cmd)
            if ret != 0:
                print('ERROR: There was an error while running cargo.' +
                      ' See the cargo.out file for details.')

    def generate_gn(self):
        """Parse cargo.out and generate BUILD.gn files."""
        cargo_out = 'cargo.out'  # The file name used to save cargo build -v output.
        errors_line = 'Errors in ' + cargo_out + ':'
        if self.dry_run:
            print('Dry-run skip: read', cargo_out, 'write BUILD.gn')
        elif os.path.exists(cargo_out):
            self.find_root_pkg()
            with open(cargo_out, 'r') as cargo_out:
                self.parse(cargo_out, 'BUILD.gn')
                self.crates.sort(key=get_crate_name)
                for crate in self.crates:
                    crate.dump()
                if self.error_infos:
                    self.append_to_gn('\n' + errors_line + '\n' + self.error_infos)
                if self.test_error_infos:
                    self.append_to_gn('\n// Errors when listing tests:\n' +
                                      self.test_error_infos)
        return self

    def find_root_pkg(self):
        """Read name of [package] in ./Cargo.toml."""
        if os.path.exists('./Cargo.toml'):
            return
        with open('./Cargo.toml', 'r') as infile:
            get_designated_pkg_info(infile, 'name')

    def parse(self, infile, outfile_name):
        """Parse rustc, test, and warning messages in infile, return a list of Crates."""
        # cargo test --list output of the start of running a binary.
        cargo_test_list_start_re = re.compile('^\s*Running (.*) \(.*\)$')
        # cargo test --list output of the end of running a binary.
        cargo_test_list_end_re = re.compile('^(\d+) tests, (\d+) benchmarks$')
        compiling_pat = re.compile('^ +Compiling (.*)$')
        current_test_name = None
        for line in infile:
            # We read the file in two passes, where the first simply checks for empty tests.
            # Otherwise we would add and merge tests before seeing they're empty.
            if cargo_test_list_start_re.match(line):
                current_test_name = cargo_test_list_start_re.match(line).group(1)
            elif current_test_name and cargo_test_list_end_re.match(line):
                match = cargo_test_list_end_re.match(line)
                if int(match.group(1)) + int(match.group(2)) == 0:
                    self.add_empty_test(current_test_name)
                current_test_name = None
            #Get Compiling information
            if compiling_pat.match(line):
                self.add_deps_libname_map(compiling_pat.match(line).group(1))
        infile.seek(0)
        self.parse_cargo_out(infile, outfile_name)

    def add_empty_test(self, name):
        if name == 'unittests':
            self.empty_unittests = True
        else:
            self.empty_tests.add(name)

    def add_deps_libname_map(self, line):
        line_list = line.split()
        if len(line_list) > 1:
            self.deps_libname_map[pkg_to_crate_name(line_list[0])] = line_list[0]

    def parse_cargo_out(self, infile, outfile_name):
        # Cargo -v output of a call to rustc.
        rustc_re = re.compile('^ +Running `rustc (.*)`$')
        # Cargo -vv output of a call to rustc could be split into multiple lines.
        # Assume that the first line will contain some CARGO_* env definition.
        rustc_vv_re = re.compile('^ +Running `.*CARGO_.*=.*$')
        # Rustc output of file location path pattern for a warning message.
        warning_output_file_re = re.compile('^ *--> ([^:]*):[0-9]+')
        cargo_to_gn_running_re = re.compile('^### Running: .*$')
        line_num = 0
        previous_warning = False  # true if the previous line was warning
        rustc_line = ''           # previous line matching rustc_vv_re
        in_tests = False
        for line in infile:
            line_num += 1
            if line.startswith('warning: '):
                previous_warning = True
                rustc_line = self.assert_empty_rustc_line(rustc_line)
                continue
            new_rustc_line = ''
            if rustc_re.match(line):
                args_line = rustc_re.match(line).group(1)
                self.add_crate(Crate(self, outfile_name).parse_rustc(line_num, args_line))
                self.assert_empty_rustc_line(rustc_line)
            elif rustc_line or rustc_vv_re.match(line):
                new_rustc_line = self.deal_rustc_command(
                    line_num, rustc_line, line, outfile_name)
            elif previous_warning and warning_output_file_re.match(line):
                file_path = warning_output_file_re.match(line).group(1)
                if file_path[0] != '/':  # ignore absolute path
                    self.warning_files.add(file_path)
                self.assert_empty_rustc_line(rustc_line)
            elif line.startswith('error: ') or line.startswith('error[E'):
                if not self.args.ignore_cargo_errors:
                    self.add_error_infos(in_tests, line)
            elif cargo_to_gn_running_re.match(line):
                in_tests = "cargo test" in line and "--list" in line
            previous_warning = False
            rustc_line = new_rustc_line

    def assert_empty_rustc_line(self, line):
        # report error if line is not empty
        if line:
            self.append_to_gn('ERROR -vv line: ' + line)
        return ''

    def append_to_gn(self, line):
        self.init_gn_file('BUILD.gn')
        with open('BUILD.gn', 'a') as outfile:
            outfile.write(line)
        print(line)

    def init_gn_file(self, name):
        # name could be BUILD.gn or sub_dir_path/BUILD.gn
        if name in self.gn_files:
            return
        self.gn_files.add(name)
        if os.path.exists(name):
            os.remove(name)
        with open(name, 'w') as outfile:
            outfile.write(BUILD_GN_HEADER)
            outfile.write('\n')
            outfile.write('import("%s")\n' % IMPORT_CONTENT)

    def add_error_infos(self, in_tests, line):
        if in_tests:
            self.test_error_infos += '// '.join(line)
        else:
            self.error_infos += line

    def deal_rustc_command(self, line_num, rustc_line, line, outfile_name):
        """Process a rustc command line from cargo -vv output."""
        # cargo build -vv output can have multiple lines for a rustc command due to '\n' in strings
        # for environment variables. strip removes leading spaces and '\n' at the end
        new_rustc_line = (rustc_line.strip() + line) if rustc_line else line
        # The combined -vv output rustc command line pattern.
        rustc_vv_cmd_args = re.compile('^ *Running `.*CARGO_.*=.* rustc (.*)`$')
        if not line.endswith('`\n') or (new_rustc_line.count('`') % 2) != 0:
            return new_rustc_line
        if rustc_vv_cmd_args.match(new_rustc_line):
            args = rustc_vv_cmd_args.match(new_rustc_line).group(1)
            self.add_crate(Crate(self, outfile_name).parse_rustc(line_num, args))
        else:
            self.assert_empty_rustc_line(new_rustc_line)
        return ''

    def add_crate(self, new_crate):
        """Merge crate with someone in crates, or append to it. Return crates."""
        if (is_build_script(new_crate.crate_name) and
            not is_dependent_path(new_crate.main_src) and
            new_crate.root_pkg_name and len(new_crate.deps) > 0):
            self.build_deps[new_crate.root_pkg_name] = new_crate.deps
        if new_crate.skip_crate():
            # include debug info of all crates
            if self.args.debug:
                self.crates.append(new_crate)
        else:
            for crate in self.crates:
                if crate.merge_crate(new_crate, 'BUILD.gn'):
                    return
            # If not merged, decide module type and name now.
            new_crate.decide_module_type()
            self.crates.append(new_crate)

    def should_ignore_test(self, src):
        # cargo test outputs the source file for integration tests but "unittests" for unit tests.
        # To figure out to which crate this corresponds, we check if the current source file is
        # the main source of a non-test crate, e.g., a library or a binary.
        return (src in self.empty_tests or src in self.args.test_blocklist or
                (self.empty_unittests and
                 src in [c.main_src for c in self.crates if c.crate_types != ['test']]))


def get_arg_parser():
    """Parse main arguments."""
    argparser = argparse.ArgumentParser('cargo2gn')
    argparser.add_argument('--add-workspace', action='store_true', default=False,
        help=('append [workspace] to Cargo.toml before calling cargo, to treat' +
              ' current directory as root of package source; otherwise the relative' +
              ' source file path in generated .gn file will be from the parent directory.'))
    argparser.add_argument('--cargo', action='append', metavar='args_string',
        help=('extra cargo build -v args in a string, ' +
              'each --cargo flag calls cargo build -v once'))
    argparser.add_argument('--cargo-bin', type=str,
        help='use cargo in the cargo_bin directory instead of the prebuilt one')
    argparser.add_argument('--config', type=str,
        help=('Load command-line options from the given config file. ' +
              'Options in this file will override those passed on the command line.'))
    argparser.add_argument('--copy-out', action='store_true', default=False,
        help=('only for root directory, copy build.rs output to ./out/* and ' +
              'add a genrule to copy ./out/*.'))
    argparser.add_argument('--debug', action='store_true', default=False,
        help='dump debug info into BUILD.gn')
    argparser.add_argument('--dependency-blocklist', nargs='*', default=[],
        help='Do not emit the given dependencies (without lib prefixes).')
    argparser.add_argument('--features', type=str,
        help=('pass features to cargo build, ' +
              'empty string means no default features'))
    argparser.add_argument('--ignore-cargo-errors', action='store_true', default=False,
        help='do not append cargo/rustc error messages to BUILD.gn')
    argparser.add_argument('--no-pkg-info', action='store_true', default=False,
        help='Do not attempt to determine the package info automatically.')
    argparser.add_argument('--no-subdir', action='store_true', default=False,
        help='do not output anything for sub-directories')
    argparser.add_argument('--one-file', action='store_true', default=False,
        help=('output all into one BUILD.gn, default will generate one BUILD.gn ' +
              'per Cargo.toml in subdirectories'))
    argparser.add_argument('--run', action='store_true', default=False,
        help='run it, default is dry-run')
    argparser.add_argument('--rustflags', type=str, help='passing flags to rustc')
    argparser.add_argument('--skipcargo', action='store_true', default=False,
        help='skip cargo command, parse cargo.out, and generate BUILD.gn')
    argparser.add_argument('--test-blocklist', nargs='*', default=[],
        help=('Do not emit the given tests. ' +
              'Pass the path to the test file to exclude.'))
    argparser.add_argument('--use-cargo-lock', action='store_true', default=False,
        help=('run cargo build with existing Cargo.lock ' +
              '(used when some latest dependent crates failed)'))
    argparser.add_argument('--vv', action='store_true', default=False,
        help='run cargo with -vv instead of default -v')
    return argparser


def get_parse_args(argparser):
    """Parses command-line options."""
    args = argparser.parse_args()
    # Use the values specified in a config file if one was found.
    if args.config:
        with open(args.config, 'r') as file:
            config_data = json.load(file)
            args_dict = vars(args)
            for arg in config_data:
                args_dict[arg.replace('-', '_')] = config_data[arg]
    return args


def main():
    argparser = get_arg_parser()
    args = get_parse_args(argparser)
    if not args.run:  # default is dry-run
        print(DRY_RUN_CONTENT)
    Runner(args).run_cargo().generate_gn()


if __name__ == '__main__':
    main()
