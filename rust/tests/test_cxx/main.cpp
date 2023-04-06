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
#include <iostream>
#include "lib.rs.h"

int main(int argc, const char* argv[])
{
    int a = 2021;
    int b = 4;
    print_message_in_rust();
    std::cout << r_return_primitive() << std::endl;
    std::cout << r_return_shared().z << std::endl;
    std::cout << std::string(r_return_rust_string()) << std::endl;
    std::cout << r_return_sum(a, b) << std::endl;
    return 0;
}