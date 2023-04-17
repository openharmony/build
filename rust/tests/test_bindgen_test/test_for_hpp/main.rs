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

//!  bindgen test for hpp
#![allow(clippy::approx_constant)]
#![allow(non_snake_case)]
mod c_ffi {
    #![allow(dead_code)]
    #![allow(non_upper_case_globals)]
    #![allow(non_camel_case_types)]
    include!(env!("BINDGEN_RS_FILE"));
}


fn bindgen_test_layout_C() {
    const UNINIT: ::std::mem::MaybeUninit<c_ffi::C> =
        ::std::mem::MaybeUninit::uninit();
    let ptr = UNINIT.as_ptr();
    println!(
        "The mem size of c_ffi::C is {} usize",
        ::std::mem::size_of::<c_ffi::C>()
    );
    println!(
        "The align_of size of c_ffi::C is {} usize",
        ::std::mem::align_of::<c_ffi::C>()
    );
    println!(
        "The addr_of!((*ptr).c) as usize - ptr as usize is {} usize",
        unsafe { ::std::ptr::addr_of!((*ptr).c) as usize - ptr as usize }
    );
    println!(
        "The addr_of!((*ptr).ptr) as usize - ptr as usize is {} usize",
        unsafe { ::std::ptr::addr_of!((*ptr).ptr) as usize - ptr as usize }
    );
    println!(
        "The addr_of!((*ptr).arr) as usize - ptr as usize is {} usize",
        unsafe { ::std::ptr::addr_of!((*ptr).arr) as usize - ptr as usize }
    );
    println!(
        "The addr_of!((*ptr).d) as usize - ptr as usize is {} usize",
        unsafe { ::std::ptr::addr_of!((*ptr).d) as usize - ptr as usize }
    );
    println!(
        "The addr_of!((*ptr).other_ptr) as usize - ptr as usize is {} usize",
        unsafe {
            ::std::ptr::addr_of!((*ptr).other_ptr) as usize - ptr as usize
        }
    );
}


fn bindgen_test_layout_D() {
    const UNINIT: ::std::mem::MaybeUninit<c_ffi::D> =
        ::std::mem::MaybeUninit::uninit();
    let ptr = UNINIT.as_ptr();
    println!(
        "The mem size of c_ffi::D is {} usize",
        ::std::mem::size_of::<c_ffi::D>()
    );
    println!(
        "The align_of size of c_ffi::D is {} usize",
        ::std::mem::align_of::<c_ffi::D>()
    );
    println!(
        "The addr_of!((*ptr).ptr) as usize - ptr as usize is {} usize",
        unsafe { ::std::ptr::addr_of!((*ptr).ptr) as usize - ptr as usize }
    );
}
impl Default for c_ffi::D {
    fn default() -> Self {
        let mut r = ::std::mem::MaybeUninit::<Self>::uninit();
        unsafe {
            ::std::ptr::write_bytes(r.as_mut_ptr(), 0, 1);
            r.assume_init()
        }
    }
}

/// fn main()
fn main() {
    bindgen_test_layout_C();
    bindgen_test_layout_D()
}
