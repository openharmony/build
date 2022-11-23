pub struct RustLogMessageDylib {
    pub dy_id: i32,
    pub dy_msg: String,
}

pub fn rust_log_dylib(msg: RustLogMessageDylib) {
    println!("id:{} message:{:?}", msg.dy_id, msg.dy_msg)
}
