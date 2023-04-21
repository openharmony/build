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

#ifndef BUILD_RUST_TESTS_BINDGEN_TEST_LIB_H_
#define BUILD_RUST_TESTS_BINDGEN_TEST_LIB_H_

// bindgen-flags: --with-derive-hash --with-derive-partialeq --with-derive-eq
typedef int SecondInt;

class C {
public:
    typedef int FirstInt;
    typedef const char* Lookup;
    FirstInt c;
    FirstInt* ptr;
    FirstInt arr[10];
    SecondInt d;
    SecondInt* other_ptr;

    void method(FirstInt c);
    void methodRef(FirstInt& c);
    void complexMethodRef(Lookup& c);
    void anotherMethod(SecondInt c);
};

class D : public C {
public:
    FirstInt* ptr;
};

#endif  //  BUILD_RUST_TESTS_BINDGEN_TEST_LIB_H_