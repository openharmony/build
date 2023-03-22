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

#ifndef BUILD_RUST_TESTS_AUTOCXX_RUST_CALL_CPP_INPUT_H_
#define BUILD_RUST_TESTS_AUTOCXX_RUST_CALL_CPP_INPUT_H_
#include <cstdint>
#include <sstream>
#include <stdint.h>
#include <string>
#define multiply_by_triple 3

class Dog {
public:
    Dog() : friends(0) {}
    void add_a_friends();
    std::string say() const;
private:
    uint32_t friends;
};

inline uint32_t DoMath(uint32_t a)
{
    return a * multiply_by_triple;
}

inline void Dog::add_a_friends()
{
    friends++;
}
inline std::string Dog::say() const
{
    std::ostringstream oss;
    std::string plural = friends == 1 ? "" : "s";
    oss << "This goat has " << friends << " horn" << plural << ".";
    return oss.str();
}
#endif