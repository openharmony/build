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

//! test_rlib_cargo_crate
use std::env;
use std::path::Path;
use std::io::Write;
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

    let feature_a = env::var_os("CARGO_FEATURE_MY_FEATURE_A").is_some();
    if feature_a {
        println!("cargo:rustc-cfg=has_feature_a");
    }
    let feature_b = env::var_os("CARGO_FEATURE_MY_FEATURE_B").is_some();
    if feature_b {
        println!("cargo:rustc-cfg=has_feature_b");
    }

    // Some tests as to whether we're properly emulating various cargo features.
    assert!(Path::new("build.rs").exists());
    assert!(Path::new(&env::var_os("CARGO_MANIFEST_DIR").unwrap()).join("build.rs").exists());
    assert!(Path::new(&env::var_os("OUT_DIR").unwrap()).exists());

    // Confirm the following env var is set
    env::var_os("CARGO_CFG_TARGET_ARCH").unwrap();

    generate_some_code().unwrap();
}

fn generate_some_code() -> std::io::Result<()> {
    let test_output_dir = Path::new(&env::var_os("OUT_DIR").unwrap()).join("generated");
    let _ = std::fs::create_dir_all(&test_output_dir);
    // Test that environment variables from .gn files are passed to build scripts
    let preferred_number = env::var("ENV_VAR_FOR_BUILD_SCRIPT").unwrap();
    let mut file = std::fs::File::create(test_output_dir.join("generated.rs"))?;
    write!(file, "fn run_some_generated_code() -> u32 {{ {} }}", preferred_number)?;
    Ok(())
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
