extern crate rust_log;

use rust_log::RustLogMessage;
use rust_log::rust_log;

fn main() {
    let msg : RustLogMessage = RustLogMessage {id: 0, msg: "string in rlib crate".to_string()};
    rust_log(msg);
    println!("Hello, world!");
}
// fn main() {
//     println!("hello, world!");
// }