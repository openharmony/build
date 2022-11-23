extern crate simple_printer_rlib;

use simple_printer_rlib::RustLogMessage;
use simple_printer_rlib::rust_log_rlib;

fn main() {
    let msg : RustLogMessage = RustLogMessage {id: 0, msg: "string in rlib crate".to_string()};
    rust_log_rlib(msg);
}