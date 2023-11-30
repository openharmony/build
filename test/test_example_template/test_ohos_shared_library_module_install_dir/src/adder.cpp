/*
 * Copyright (c) 2023 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <iostream>

static const uint32_t ip_ida = 10;
static const uint32_t ip_idb = 20;
static const uint32_t ip_idc = 30;

using namespace std;
class Adder {
public:
    explicit Adder(int i = 0)
    {
        total = i;
    }
    void addNum(int number)
    {
        total += number;
    }
    int getTotal()
    {
        return total;
    }
private:
    int total;
}
int main()
{
    Adder a;
    a.addNum(ip_ida);
    a.addNum(ip_idb);
    a.addNum(ip_idc);
    cout << "Total " << a.getTotal() << endl;
    return 0;
}