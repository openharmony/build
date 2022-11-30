extern crate derive_helper_macro;
use derive_helper_macro::HelperAttr;

#[derive(HelperAttr)]
struct Struct {
    #[helper] field: ()
}

fn main() {
}
