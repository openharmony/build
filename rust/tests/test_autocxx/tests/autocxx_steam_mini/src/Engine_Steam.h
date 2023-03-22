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
#ifndef BUILD_RUST_TESTS_AUTOCXX_STEAM_MINI_INPUT_H_
#define BUILD_RUST_TESTS_AUTOCXX_STEAM_MINI_INPUT_H_
constexpr int UserId = 42;

#include <iostream>

class IEngine {
public:
	virtual int ConnectWithGlobalUser(int) = 0;
    virtual void DisconnectWithGlobalUser(int userId) = 0;
    virtual ~IEngine() = default;
};

class Engine_Steam : public IEngine {
    int ConnectWithGlobalUser(int userId) final
    {
        std::cout << "ConnectWithGlobalUser, passed " << userId << std::endl;
        return UserId;
    }
    void DisconnectWithGlobalUser(int userId) final
    {
        std::cout << "DisconnectWithGlobalUser, passed " << userId << std::endl;
    }
};

void* GetSteamEngine(void)
{
    return new Engine_Steam();
}
#endif