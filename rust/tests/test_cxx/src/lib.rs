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

//! fdhjhj
#[cxx::bridge]
mod ffi{
    #![allow(dead_code)]
    #[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
    struct Shared {
        z: usize,
    }
    // unsafe extern "C++" {
    //     fn c_return_rust_vec_string() -> Vec<String>;
    // }
    
    extern "Rust"{
        type R;
        fn print_message_in_rust();
        fn r_return_primitive() -> usize;
        fn r_return_shared() -> Shared;
        fn r_return_box() -> Box<R>;
        fn r_return_rust_string() -> String;
        // fn r_return_unique_ptr_string() -> UniquePtr<CxxString>;
        fn get(self: &R) -> usize;
        fn set(self: &mut R, n: usize) -> usize;
        fn r_return_sum(_: usize, _: usize) -> usize;
    }
}
// use cxx::UniquePtr;
// use cxx::CxxString;
///  sd
#[derive(PartialEq, Debug)]
pub struct R(pub usize);

impl R {
    fn get(&self) -> usize {
        self.0
    }

    fn set(&mut self, n: usize) -> usize {
        self.0 = n;
        n
    }
}




fn print_message_in_rust(){
    println!("Here is a message from Rust.")
}
fn r_return_primitive() -> usize {
    2020
}
fn r_return_shared() -> ffi::Shared {
    ffi::Shared { z: 2020 }
}

fn r_return_box() -> Box<R> {
    Box::new(R(2020))
}

fn r_return_rust_string() -> String {
    "2020".to_owned()
}

fn r_return_sum(n1: usize, n2: usize) -> usize {
    n1 + n2
}



// fn r_return_unique_ptr_string() -> UniquePtr<CxxString> {
//     extern "C" {
//         fn cxx_test_suite_get_unique_ptr_string() -> *mut CxxString;
//     }
//     unsafe { UniquePtr::from_raw(cxx_test_suite_get_unique_ptr_string()) }
// }