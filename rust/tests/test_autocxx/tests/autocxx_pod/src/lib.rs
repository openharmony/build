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

//! autocxx demo for pod data
use autocxx::prelude::*;

include_cpp! {
    #include "build/rust/tests/test_autocxx/tests/autocxx_pod/src/Rectangle.h"
    safety!(unsafe)
    generate_pod!("Rectangle")
    generate!("output_point")
}

use ffi::{Point_x_y, Rectangle};

/// pub fn autocxx_pod_func()
pub fn autocxx_pod_func() {
    let r = Rectangle {
        left_top: Point_x_y { x: 3, y: 3 },
        right_bottom: Point_x_y { x: 12, y: 15 },
    };
    let center = Point_x_y {
        x: r.left_top.x + r.get_width().0 / 2,
        y: r.left_top.y + r.get_height().0 / 2,
    };
    ffi::output_point(center);
}


/// autocxx pod test main
fn main() {
    autocxx_pod_func();
}