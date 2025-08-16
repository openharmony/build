#!/bin/bash
# Copyright (c) 2021 Huawei Device Co., Ltd.
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
MAX_RETRIES=50
COMMAND_TO_RUN=("$@")
 
for i in $(seq 1 $MAX_RETRIES); do
  echo "Taihe attempt $i/$MAX_RETRIES: Executing command..."
  echo "--> ${COMMAND_TO_RUN[@]}"
 
  "${COMMAND_TO_RUN[@]}"
  
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "Taihe build success"
    exit 0
  fi
 
  sleep 0.1
done
 
set -e
echo "Taihe build fail"
exit 1
