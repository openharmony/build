#!/bin/bash
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

set -e

function install_pytest() {
    if ! command -v pytest &> /dev/null; then
        echo "Installing pytest..."
        python -m pip install pytest "$@"
    else
        echo "pytest is already installed."
    fi
}

function install_pytest_html() {
    if ! pip show pytest-html &> /dev/null; then
      echo "Installing pytest-html..."
      python -m pip install pytest-html "$@"
    else
        echo "pytest-html is already installed."
    fi
}

function install_pytest_metadata() {
    if ! pip show pytest-metadata &> /dev/null; then
        echo "Installing pytest-metadata..."
        python -m pip install pytest-metadata "$@"
    else
        echo "pytest-metadata is already installed."
    fi
}

function install_py() {
    if ! pip show py &> /dev/null; then
        echo "Installing py..."
        python -m pip install py "$@"
    else
        echo "py is already installed."
    fi
}

function install() {
    install_pytest "$@"
    install_pytest_html "$@"
    install_pytest_metadata "$@"
    install_py "$@"
}

function start() {
    if [[ $# -eq 2 && $1 == "-i" ]]; then
        install "$@"
    elif [[ $# -eq 0 ]]; then
        install "$@"
    else
        echo "args wrong"
    fi
}

start "$@"
