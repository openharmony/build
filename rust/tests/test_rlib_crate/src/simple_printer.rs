/*
 * Copyright (c) 2022 Huawei Device Co., Ltd.
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

//! simple_printer

/// struct RustLogMessage

pub struct RustLogMessage {
    /// i32: id
    pub id: i32,
    /// String: msg
    pub msg: String,
}

/// function rust_log_rlib
pub fn rust_log_rlib(msg: RustLogMessage) {
    println!("id:{} message:{:?}", msg.id, msg.msg)
}
