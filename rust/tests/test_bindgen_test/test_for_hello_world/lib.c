/*
 * Copyright (c) 2023 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "build/rust/tests/test_bindgen_test/test_for_hello_world/lib.h"
#include <stdint.h>
#include <stdio.h>

void say_hello(const char *message) {
  printf("%s from C\n", message);
}
uint32_t func_a_add_b(uint32_t a, uint32_t b)
{
    return a + b;
}
