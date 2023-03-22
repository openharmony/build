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

//! test for extern "C"
#![allow(clippy::approx_constant)]
use std::os::raw::c_double;
use std::os::raw::c_int;

extern "C" {
    fn abs(num: c_int) -> c_int;
    fn sqrt(num: c_double) -> c_double;
    fn pow(num: c_double, power: c_double) -> c_double;
}

/// fn main()
fn main() {
    let x: i32 = -123;
    println!("This is an example of calling a C library function from Rust:");
    println!("{x}的绝对值是: {}.", unsafe { abs(x) });
    let n: f64 = 9.0;
    let p: f64 = 3.0;
    println!("{n}的{p}次方是: {}.", unsafe { pow(n, p) });
    let mut y: f64 = 64.0;
    println!("{y}的平方根是: {}.", unsafe { sqrt(y) });
    y = -3.14;
    println!("{y}的平方根是: {}.", unsafe { sqrt(y) });
}
