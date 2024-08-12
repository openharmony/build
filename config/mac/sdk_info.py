#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import doctest
import itertools
import os
import subprocess
import sys

# This script prints information about the build system, the operating
# system and the iOS or Mac SDK (depending on the platform "iphonesimulator",
# "iphoneos" or "macosx" generally).


def split_version(version: str or bytes):
    """
    Splits the Xcode version to 3 values.

    >>> list(split_version('8.2.1.1'))
    ['8', '2', '1']
    >>> list(split_version('9.3'))
    ['9', '3', '0']
    >>> list(split_version('10.0'))
    ['10', '0', '0']
    """
    if isinstance(version, bytes):
        version = version.decode()
    version = version.split('.')
    return itertools.islice(itertools.chain(version, itertools.repeat('0')), 0, 3)


def format_version(version: str or bytes):
    """
    Converts Xcode version to a format required for DTXcode in Info.plist

    >>> format_version('8.2.1')
    '0821'
    >>> format_version('9.3')
    '0930'
    >>> format_version('10.0')
    '1000'
    """
    major, minor, patch = split_version(version)
    return ('%2s%s%s' % (major, minor, patch)).replace(' ', '0')


def fill_xcode_version(fill_settings: dict) -> dict:
    """Fills the Xcode version and build number into |fill_settings|."""

    try:
        lines = subprocess.check_output(['xcodebuild', '-version']).splitlines()
        fill_settings['xcode_version'] = format_version(lines[0].split()[-1])
        fill_settings['xcode_version_int'] = int(fill_settings['xcode_version'], 10)
        fill_settings['xcode_build'] = lines[-1].split()[-1]
    except subprocess.CalledProcessError as cpe:
        print(f"Failed to run xcodebuild -version: {cpe}")


def fill_machine_os_build(fill_settings: dict):
    """Fills OS build number into |fill_settings|."""
    fill_settings['machine_os_build'] = subprocess.check_output(
        ['sw_vers', '-buildVersion']).strip()


def fill_sdk_path_and_version(fill_settings: dict, platform: str, xcode_version: str or bytes):
    """Fills the SDK path and version for |platform| into |fill_settings|."""
    fill_settings['sdk_path'] = subprocess.check_output([
        'xcrun', '-sdk', platform, '--show-sdk-path']).strip()
    fill_settings['sdk_version'] = subprocess.check_output([
        'xcrun', '-sdk', platform, '--show-sdk-version']).strip()
    fill_settings['sdk_platform_path'] = subprocess.check_output([
        'xcrun', '-sdk', platform, '--show-sdk-platform-path']).strip()
    if xcode_version >= '0720':
        fill_settings['sdk_build'] = subprocess.check_output([
          'xcrun', '-sdk', platform, '--show-sdk-build-version']).strip()
    else:
        fill_settings['sdk_build'] = fill_settings['sdk_version']


if __name__ == '__main__':
    doctest.testmod()

    parser = argparse.ArgumentParser()
    parser.add_argument("--developer_dir", required=False)
    args, unknownargs = parser.parse_known_args()
    if args.developer_dir:
        os.environ['DEVELOPER_DIR'] = args.developer_dir

    if len(unknownargs) != 1:
        sys.stderr.write(
          'usage: %s [iphoneos|iphonesimulator|macosx]\n' %
          os.path.basename(sys.argv[0]))
        sys.exit(1)

    settings = {}
    fill_machine_os_build(settings)
    fill_xcode_version(settings)
    try:
        fill_sdk_path_and_version(settings, unknownargs[0], settings.get('xcode_version'))
    except ValueError as vle:
        print(f"Error: {vle}")

    for key in sorted(settings):
        value = settings.get(key)
        if isinstance(value, bytes):
            value = value.decode()
        if key != 'xcode_version_int':
            value = '"%s"' % value
            print('%s=%s' % (key, value))
        else:
            print('%s=%d' % (key, value))
