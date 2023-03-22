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

//! autocxx test for steam mini
use autocxx::prelude::*;

include_cpp! {
    #include "build/rust/tests/test_autocxx/tests/autocxx_steam_mini/src/Engine_Steam.h"
    safety!(unsafe)
    generate!("GetSteamEngine")
    generate!("IEngine")
}

/// pub fn autocxx_steam_mini()
pub fn autocxx_steam_mini() {
    let steam_engine = ffi::GetSteamEngine();
    let steam_engine = steam_engine as *mut ffi::IEngine;
    let mut steam_engine = unsafe { std::pin::Pin::new_unchecked(&mut *steam_engine) };
    steam_engine
        .as_mut()
        .ConnectWithGlobalUser(autocxx::c_int(12));
    steam_engine
        .as_mut()
        .DisconnectWithGlobalUser(autocxx::c_int(12));
}


/// autocxx_steam_mini main
fn main() {
    autocxx_steam_mini();
}
