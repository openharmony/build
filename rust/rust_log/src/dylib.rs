pub struct RustLogMessage {
    pub id: i32,
    pub msg: String,
}

pub fn rust_log(msg: RustLogMessage) {
    println!("id:{} message:{:?}", msg.id, msg.msg)
}
