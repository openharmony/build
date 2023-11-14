import subprocess
import os
import pytest


@pytest.fixture()
def init_build_env():
    def find_top_dir():
        cur_dir = os.getcwd()
        while cur_dir != "/":
            build_scripts = os.path.join(
                cur_dir, 'build/scripts/build_package_list.json')
            if os.path.exists(build_scripts):
                return cur_dir
            cur_dir = os.path.dirname(cur_dir)

    os.chdir(find_top_dir())
    subprocess.run(['repo', 'forall', '-c', 'git reset --hard'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(['repo', 'forall', '-c', 'git clean -dfx'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class TestModuleBuild():
    def test_ohos_shared_library(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/tests/module_build/test_ohos_shared_library'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert "build test_ohos_shared_library failed"

    def test_ohos_static_library(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/tests/module_build/test_ohos_static_library'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_ohos_static_library failed"

    def test_ohos_executable(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/tests/module_build/test_ohos_executable'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_ohos_static_library failed"

    def ohos_source_set(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/tests/module_build/test_ohos_source_set'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build ohos_source_set failed"


class TestHapBuild():
    def test_ohos_app(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/tests/unittest/MyApplication3:MyApplication3'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_ohos_app failed"


class TestRustBuild:
    def test_bin_cargo_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_bin_cargo_crate:test_bin_cargo_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_bin_cargo_crate fail"

    def test_bin_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_bin_crate:test_bin_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        result_path = "../../out/rk3568/build/build_framework/test_bin_crate"
        assert proc.returncode == 0, "build test_bin_crate failed"

    def test_for_extern_c(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_bindgen_test/test_for_extern_c:test_extern_c'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_for_extern_c failed"

    def test_for_h(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_bindgen_test/test_for_h:bindgen_test_for_h'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_for_h failed"

    def test_for_hello_world(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_bindgen_test/test_for_hello_world:bindgen_test'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        assert proc.returncode == 0, "build test_for_hello_world failed"

    def test_for_hpp(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_bindgen_test/test_for_hpp:bindgen_test_hpp'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_for_hpp failed"

    def test_cdylib_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_cdylib_crate:test_cdylib_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_cdylib_crate failed"

    def test_cxx(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_cxx:test_cxx_exe'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_cxx_examp_rust failed"

    def test_cxx_rust(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_cxx_rust:test_cxx_rust'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_cxx_rust failed"

    def test_dylib_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_dylib_crate:test_dylib_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_dylib_crate failed"

    def test_idl(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_idl:test_idl'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_idl failed"

    def test_proc_macro_cargo_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_proc_macro_cargo_crate:test_proc_macro_cargo_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_proc_macro_cargo_crate failed"

    def test_attribute_macro(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_proc_macro_crate/test_attribute_macro:test_attribute_macro'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_attribute_macro failed"

    def test_derive_helper_macro(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_proc_macro_crate/test_derive_helper_macro:test_derive_helper_macro'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_derive_helper_macro failed"

    def test_function_macro(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_proc_macro_crate/test_function_macro:test_function_macro'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_function_macro failed"

    def test_derive_macro(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_proc_macro_crate/test_derive_macro:test_derive_macro'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_function_macro failed"

    def test_rlib_cargo_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target',
                                 'build/rust/tests/test_rlib_cargo_crate:test_rlib_crate_associated_bin'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build simple_printer_staticlib failed"

    def test_rlib_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_rlib_crate:test_rlib_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_rlib_crate failed"

    def test_rust_st(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_rust_st:test_rust_st'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build simple_printer_staticlib failed"

    def test_rust_ut(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_rust_ut:test_rust_ut'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build simple_printer_staticlib failed"

    def test_static_link(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_static_link:test_static_link'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build test_static_link failed"

    def test_staticlib_crate(self):
        proc = subprocess.Popen(['../../build.sh', '--product-name', 'rk3568',
                                 '--build-target', 'build/rust/tests/test_staticlib_crate:test_staticlib_crate'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        assert proc.returncode == 0, "build simple_printer_staticlib failed"

