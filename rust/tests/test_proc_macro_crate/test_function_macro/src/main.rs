extern crate function_macro;
use function_macro::make_answer;

make_answer!();

fn main() {
    println!("{}", answer());
}
