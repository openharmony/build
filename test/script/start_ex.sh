#!/bin/bash

root_path=""
generate_build_dir(){
  script_path=$(cd $(dirname $0);pwd)
  pre_dir_path=$(dirname ${script_path})
  pre_dir_path=$(dirname ${pre_dir_path})
  root_path=$(dirname ${pre_dir_path})

  mkdir -p $root_path/out/rk3568/obj/build
}

generate_build_option_report() {
    build_option_example_file=$1
    pytest -vs --html $root_path/out/rk3568/obj/build/build_option_report.html $root_path/build/test/example/$build_option_example_file
    pkill -f '/pyd.py --root .*/.pycache --start'
}

generate_gn_template_report() {
    gn_template_example_file=$1
    pytest -vs --html $root_path/out/rk3568/obj/build/gn_template_report.html $root_path/build/test/example/$gn_template_example_file
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

generate_build_dir
start "$@"




