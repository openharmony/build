extern crate simple_printer_dylib;

use simple_printer_dylib::RustLogMessage;
use simple_printer_dylib::rust_log_dylib;

fn main() {
    let msg : RustLogMessage = RustLogMessage {id: 0, msg: "string in rlib crate".to_string()};
    rust_log_dylib(msg);
}