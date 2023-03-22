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

//!  bindgen test
#![allow(clippy::approx_constant)]
#![allow(clippy::eq_op)]
mod c_ffi {
    #![allow(dead_code)]
    #![allow(non_upper_case_globals)]
    #![allow(non_camel_case_types)]
    include!(env!("BINDGEN_RS_FILE"));
  }

  fn bindgen_test_layout_foo() {
    const UNINIT: ::std::mem::MaybeUninit<c_ffi::foo> =
        ::std::mem::MaybeUninit::uninit();
    let ptr = UNINIT.as_ptr();
    println!("::std::mem::size_of::<c_ffi::foo>:{} usize",::std::mem::size_of::<c_ffi::foo>());
    println!("::std::mem::align_of::<c_ffi::foo>():{} usize",::std::mem::align_of::<c_ffi::foo>());
    println!("::std::ptr::addr_of!((*ptr).member) as usize - ptr as usize:{} usize",unsafe { ::std::ptr::addr_of!((*ptr).member) as usize - ptr as usize });
}
impl Default for c_ffi::foo {
    fn default() -> Self {
        let mut s = ::std::mem::MaybeUninit::<Self>::uninit();
        unsafe {
            ::std::ptr::write_bytes(s.as_mut_ptr(), 0, 1);
            s.assume_init()
        }
    }
}

/// fn main()
fn main() {
    bindgen_test_layout_foo();
}