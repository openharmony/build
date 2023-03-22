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

//! #[cxx::bridge]
#[cxx::bridge]
mod ffi{
    #![allow(dead_code)]
    #[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
    struct Shared {
        z: usize,
    }
    extern "Rust"{
        type R;
        fn print_message_in_rust();
        fn r_return_primitive() -> usize;
        fn r_return_shared() -> Shared;
        fn r_return_box() -> Box<R>;
        fn r_return_rust_string() -> String;
        fn get(self: &R) -> usize;
        fn set(self: &mut R, n: usize) -> usize;
        fn r_return_sum(_: usize, _: usize) -> usize;
    }
}
///  pub struct R
#[derive(PartialEq, Debug)]
pub struct R(pub usize);

impl R {
    fn set(&mut self, n: usize) -> usize {
        self.0 = n;
        n
    }

    fn get(&self) -> usize {
        self.0
    }
}


fn r_return_box() -> Box<R> {
    println!("Here is a message from Rust,test for Box<R>:");
    Box::new(R(1995))
}
fn print_message_in_rust(){
    println!("Here is a test for cpp call Rust.");
}
fn r_return_shared() -> ffi::Shared {
    println!("Here is a message from Rust,test for ffi::Shared:");
    ffi::Shared { z: 1996 }
}
fn r_return_primitive() -> usize {
    println!("Here is a message from Rust,test for usize:");
    1997
}
fn r_return_rust_string() -> String {
    println!("Here is a message from Rust,test for String");
    "Hello World!".to_owned()
}
fn r_return_sum(n1: usize, n2: usize) -> usize {
    println!("Here is a message from Rust,test for {} + {} is:",n1 ,n2);
    n1 + n2
}
