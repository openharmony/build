#!/bin/bash

if ! command -v pytest &> /dev/null; then
    echo "Installing pytest..."
    python -m pip install  pytest -i https://repo.huaweicloud.com/repository/pypi/simple/
else
    echo "pytest is already installed."
fi

if ! pip show pytest-html &> /dev/null; then
    echo "Installing pytest-html..."
    python -m pip install  pytest-html -i https://repo.huaweicloud.com/repository/pypi/simple/
else
    echo "pytest-html is already installed."
fi

if ! pip show pytest-xdist &> /dev/null; then
    echo "Installing pytest-xdist..."
    python -m pip install  pytest-xdist -i https://repo.huaweicloud.com/repository/pypi/simple/
else
    echo "pytest-xdist is already installed."
fi

if ! pip show pytest-metadata &> /dev/null; then
    echo "Installing pytest-metadata..."
    python -m pip install  pytest-metadata -i https://repo.huaweicloud.com/repository/pypi/simple/
else
    echo "pytest-metadata is already installed."
fi

if ! pip show py &> /dev/null; then
    echo "Installing py..."
    python -m pip install  py -i https://repo.huaweicloud.com/repository/pypi/simple/
else
    echo "py is already installed."
fi