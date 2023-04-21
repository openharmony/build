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
#ifndef BUILD_RUST_TESTS_CLIENT_BLOBSTORE_H
#define BUILD_RUST_TESTS_CLIENT_BLOBSTORE_H
#include <memory>
#include "cxx.h"

namespace nsp_org {
namespace nsp_blobstore {
struct MultiBufs;
struct Metadata_Blob;

class client_blobstore {
public:
    client_blobstore();
    uint64_t put_buf(MultiBufs &buf) const;
    void add_tag(uint64_t blobid, rust::Str add_tag) const;
    Metadata_Blob get_metadata(uint64_t blobid) const;

private:
    class impl;
    std::shared_ptr<impl> impl;
};

std::unique_ptr<client_blobstore> blobstore_client_new();
} // namespace nsp_blobstore
} // namespace nsp_org
#endif
