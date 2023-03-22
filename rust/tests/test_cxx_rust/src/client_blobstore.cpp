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

#include <algorithm>
#include <functional>
#include <set>
#include <string>
#include <unordered_map>
#include "src/main.rs.h"
#include "build/rust/tests/test_cxx_rust/include/client_blobstore.h"

namespace nsp_org {
namespace nsp_blobstore {
// Toy implementation of an in-memory nsp_blobstore.
//
// In reality the implementation of client_blobstore could be a large complex C++
// library.
class client_blobstore::impl {
    friend client_blobstore;
    using Blob = struct {
        std::string data;
        std::set<std::string> tags;
    };
    std::unordered_map<uint64_t, Blob> blobs;
};

client_blobstore::client_blobstore() : impl(new class client_blobstore::impl) {}

// Upload a new blob and return a blobid that serves as a handle to the blob.
uint64_t client_blobstore::put_buf(MultiBufs &buf) const
{
    std::string contents;

    // Traverse the caller's res_chunk iterator.
    //
    // In reality there might be sophisticated batching of chunks and/or parallel
    // upload implemented by the nsp_blobstore's C++ client.
    while (true) {
        auto res_chunk = next_chunk(buf);
        if (res_chunk.size() == 0) {
        break;
        }
        contents.append(reinterpret_cast<const char *>(res_chunk.data()), res_chunk.size());
    }

    // Insert into map and provide caller the handle.
    auto res = std::hash<std::string> {} (contents);
    impl->blobs[res] = {std::move(contents), {}};
    return res;
}

// Add add_tag to an existing blob.
void client_blobstore::add_tag(uint64_t blobid, rust::Str add_tag) const
{
    impl->blobs[blobid].tags.emplace(add_tag);
}

// Retrieve get_metadata about a blob.
Metadata_Blob client_blobstore::get_metadata(uint64_t blobid) const
{
    Metadata_Blob get_metadata {};
    auto blob = impl->blobs.find(blobid);
    if (blob != impl->blobs.end()) {
        get_metadata.size = blob->second.data.size();
        std::for_each(blob->second.tags.cbegin(), blob->second.tags.cend(),
                [&](auto &t) { get_metadata.tags.emplace_back(t); });
    }
    return get_metadata;
}

std::unique_ptr<client_blobstore> blobstore_client_new()
{
    return std::make_unique<client_blobstore>();
}
} // namespace nsp_blobstore
} // namespace nsp_org
