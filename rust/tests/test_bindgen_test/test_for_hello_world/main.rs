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

//!  bindgen test for hello world
#![allow(clippy::approx_constant)]
mod c_ffi {
    #![allow(dead_code)]
    #![allow(non_upper_case_globals)]
    #![allow(non_camel_case_types)]
    include!(env!("BINDGEN_RS_FILE"));
}
/// pub fn add_two_numbers_in_c
pub fn add_two_numbers_in_c(a: u32, b: u32) -> u32 {
    unsafe { c_ffi::FuncAAddB(a, b) }
}

use std::ffi::c_char;
use std::ffi::CString;

/// fn main()
fn main() {
    println!("{} + {} = {}", 3, 7, add_two_numbers_in_c(3, 7));
    let c_str = CString::new("This is a message from C").unwrap();
    let c_world: *const c_char = c_str.as_ptr() as *const c_char;
    unsafe {
        c_ffi::SayHello(c_world);
    }
}
