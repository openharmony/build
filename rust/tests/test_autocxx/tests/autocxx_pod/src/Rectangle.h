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
#ifndef BUILD_RUST_TESTS_AUTOCXX_POD_INPUT_H_
#define BUILD_RUST_TESTS_AUTOCXX_POD_INPUT_H_
#include <iostream>

struct Point_x_y {
    int x;
    int y;
};

class Rectangle {
public:
    Point_x_y left_top;
    Point_x_y right_bottom;
    int get_width() const
    {
        return right_bottom.x - left_top.x;
    }
    int get_height() const
    {
        return right_bottom.y - left_top.y;
    }
};

inline void output_point(Point_x_y p)
{
    std::cout << "(" << p.x << ", " << p.y << ")\n";
}
#endif