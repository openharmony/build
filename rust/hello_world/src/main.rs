extern crate rust_log_rlib;
extern crate rust_log_dylib;
// extern crate rust_log_proc_macro;

use rust_log_rlib::RustLogMessage;
use rust_log_rlib::rust_log_rlib;

use rust_log_dylib::RustLogMessageDylib;
use rust_log_dylib::rust_log_dylib;
//use rust_log_proc_macro::print_hello_world;

fn main() {
    let msg : RustLogMessage = RustLogMessage {id: 0, msg: "string in rlib crate".to_string()};
    rust_log_rlib(msg);
    println!("Hello, world!");
    let dy_msg : RustLogMessageDylib = RustLogMessageDylib {dy_id: 0, dy_msg: "string in dylib crate".to_string()};
    rust_log_dylib(dy_msg);
    // print_hello_world!();

}
