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
mod c_ffi {
    #![allow(dead_code)]
    #![allow(non_upper_case_globals)]
    #![allow(non_camel_case_types)]
    include!(env!("BINDGEN_RS_FILE"));
}

fn bindgen_test_layout_not_annotated() {
    const UNINIT: ::std::mem::MaybeUninit<c_ffi::NotAnnotated> =
        ::std::mem::MaybeUninit::uninit();
    let ptr = UNINIT.as_ptr();
    assert_eq!(
        ::std::mem::size_of::<c_ffi::NotAnnotated>(),
        4usize,
        concat!("Size of: ", stringify!(c_ffi::NotAnnotated))
    );
    assert_eq!(
        ::std::mem::align_of::<c_ffi::NotAnnotated>(),
        4usize,
        concat!("Alignment of ", stringify!(c_ffi::NotAnnotated))
    );
    assert_eq!(
        unsafe { ::std::ptr::addr_of!((*ptr).f) as usize - ptr as usize },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(c_ffi::NotAnnotated),
            "::",
            stringify!(f)
        )
    );
}

fn main() {
    bindgen_test_layout_not_annotated();
}
