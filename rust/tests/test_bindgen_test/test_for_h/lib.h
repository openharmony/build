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
// A few tests for enum-related issues that should be tested with all the enum
// representations.

enum Foo1 {
    BAR = 0,
    QUX
};

struct Foo2 {
    enum {
        FOOFIRST,
        FOOSECOND,
    } member;
};

/** <div rustbindgen nodebug></div> */
enum NoDebug {
    NODEBUG1,
    NODEBUG2,
};

/** <div rustbindgen derive="Debug"></div> */
enum Debug {
    DEBUG1,
    DEBUG2,
};

enum Neg {
    MINUSONE = -1,
    ONE = 1,
};

#endif  //  BUILD_RUST_TESTS_BINDGEN_TEST_LIB_H_