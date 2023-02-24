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

include!(concat!(env!("OUT_DIR"), "/generated/generated.rs"));

pub fn say_hello_from_crate() {
    assert_eq!(run_some_generated_code(), 42);
    #[cfg(is_new_rustc)]
    println!("Is new rustc");
    #[cfg(is_old_rustc)]
    println!("Is old rustc");
    #[cfg(is_ohos)]
    println!("Is ohos");
    #[cfg(is_mac)]
    println!("Is darwin");
    #[cfg(has_feature_a)]
    println!("Has feature_a");
    #[cfg(not(has_feature_a))]
    panic!("Wasn't passed feature_a");
    #[cfg(not(has_feature_b))]
    #[cfg(test_a_and_b)]
    panic!("feature_b wasn't passed");
    #[cfg(has_feature_b)]
    #[cfg(not(test_a_and_b))]
    panic!("feature_b was passed");
}

#[cfg(test)]
mod tests {
    /// Test features are passed through from BUILD.gn correctly. This test is the target configuration.
    #[test]
    #[cfg(test_a_and_b)]
    fn test_features_passed_target1() {
        #[cfg(not(has_feature_a))]
        panic!("feature a was not passed");
        #[cfg(not(has_feature_b))]
        panic!("feature b was not passed");
    }

    #[test]
    fn test_generated_code_works() {
        assert_eq!(crate::run_some_generated_code(), 42);
    }
}
