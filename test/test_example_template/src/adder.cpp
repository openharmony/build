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

static const uint32_t IP_IDA = 10;
static const uint32_t IP_IDB = 20;
static const uint32_t IP_IDC = 30;

using namespace std;
class Adder {
public:
    explicit Adder(int i = 0)
    {
        totalRes = i;
    }
    void AddNum(int numberRes)
    {
        totalRes += numberRes;
    }
    int GetTotal()
    {
        return totalRes;
    }
private:
    int totalRes;
};
int main()
{
    Adder a;
    a.AddNum(IP_IDA);
    a.AddNum(IP_IDB);
    a.AddNum(IP_IDC);
    cout << "Total " << a.GetTotal() << endl;
    return 0;
}