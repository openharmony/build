#!/bin/bash

generate_build_option_report() {
    build_option_example_file=$1
    pytest -vs --html ../out/build_option_report.html ../example/$build_option_example_file
    pkill -f '/pyd.py --root /root/.pycache --start'
}

generate_gn_template_report() {
    gn_template_example_file=$1
    pytest -vs --html ../out/gn_template_report.html ../example/$gn_template_example_file
}

start() {
    if [[ $# -eq 2 && $1 == 'test_build_option.py' && $2 == 'test_gn_template.py' ]]; then
      generate_build_option_report "$1"
      generate_gn_template_report "$2"
    elif [[ $# -eq 1 && $1 == 'test_build_option.py' ]]; then
      generate_build_option_report "$1"
    elif [[ $# -eq 1 && $1 == 'test_gn_template.py' ]]; then
      generate_gn_template_report "$1"
    else
      echo "args wrong"
    fi
}

start "$@"




