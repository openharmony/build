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

use std::env;
use std::process::Command;
use std::str::{self, FromStr};

fn main() {
    println!("cargo:rustc-cfg=build_script_ran");
    let my_minor = match rustc_minor_version() {
        Some(my_minor) => my_minor,
        None => return,
    };

    if my_minor >= 34 {
        println!("cargo:rustc-cfg=is_new_rustc");
    } else {
        println!("cargo:rustc-cfg=is_old_rustc");
    }

    let target = env::var("TARGET").unwrap();

    if target.contains("ohos") {
        println!("cargo:rustc-cfg=is_ohos");
    }
    if target.contains("darwin") {
        println!("cargo:rustc-cfg=is_mac");
    }

    // Check that we can get a `rustenv` variable from the build script.
    let _ = env!("BUILD_SCRIPT_TEST_VARIABLE");
}

fn rustc_minor_version() -> Option<u32> {
    let rustc_bin = match env::var_os("RUSTC") {
        Some(rustc_bin) => rustc_bin,
        None => return None,
    };

    let output = match Command::new(rustc_bin).arg("--version").output() {
        Ok(output) => output,
        Err(_) => return None,
    };

    let rustc_version = match str::from_utf8(&output.stdout) {
        Ok(rustc_version) => rustc_version,
        Err(_) => return None,
    };

    let mut pieces = rustc_version.split('.');
    if pieces.next() != Some("rustc 1") {
        return None;
    }

    let next_var = match pieces.next() {
        Some(next_var) => next_var,
        None => return None,
    };

    u32::from_str(next_var).ok()
}
