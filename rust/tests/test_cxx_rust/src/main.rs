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

//! test_cxx_rust
#[cxx::bridge(namespace = "nsp_org::nsp_blobstore")]
mod ffi {
    // Shared structs with fields visible to both languages.
    struct Metadata_Blob {
        size: usize,
        tags: Vec<String>,
    }

    // Rust types and signatures exposed to C++.
    extern "Rust" {
        type MultiBufs;

        fn next_chunk(buf: &mut MultiBufs) -> &[u8];
    }

    // C++ types and signatures exposed to Rust.
    unsafe extern "C++" {
        include!("build/rust/tests/test_cxx_rust/include/client_blobstore.h");

        type client_blobstore;

        fn blobstore_client_new() -> UniquePtr<client_blobstore>;
        fn put_buf(&self, parts: &mut MultiBufs) -> u64;
        fn add_tag(&self, blobid: u64, add_tag: &str);
        fn get_metadata(&self, blobid: u64) -> Metadata_Blob;
    }
}

// An iterator over contiguous chunks of a discontiguous file object.
//
// Toy implementation uses a Vec<Vec<u8>> but in reality this might be iterating
// over some more complex Rust data structure like a rope, or maybe loading
// chunks lazily from somewhere.
/// pub struct MultiBufs
pub struct MultiBufs {
    chunks: Vec<Vec<u8>>,
    pos: usize,
}
/// pub fn next_chunk
pub fn next_chunk(buf: &mut MultiBufs) -> &[u8] {
    let next = buf.chunks.get(buf.pos);
    buf.pos += 1;
    next.map_or(&[], Vec::as_slice)
}

/// fn main()
fn main() {
    let client = ffi::blobstore_client_new();

    // Upload a blob.
    let chunks = vec![b"fearless".to_vec(), b"concurrency".to_vec()];
    let mut buf = MultiBufs { chunks, pos: 0 };
    let blobid = client.put_buf(&mut buf);
    println!("blobid = {}", blobid);

    // Add a add_tag.
    client.add_tag(blobid, "rust");

    // Read back the tags.
    let get_metadata = client.get_metadata(blobid);
    println!("tags = {:?}", get_metadata.tags);
}
