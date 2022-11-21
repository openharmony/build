extern crate rust_log_rlib;

use rust_log_rlib::RustLogMessage;
use rust_log_rlib::rust_log;

fn main() {
    let msg : RustLogMessage = RustLogMessage {id: 0, msg: "string in rlib crate".to_string()};
    rust_log(msg);
    println!("Hello, world!");
}

// include "../../rust_log/src/staticlib.h"
// fn main() {
//     println!("hello, world!");
// }
