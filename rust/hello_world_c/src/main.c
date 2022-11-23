#include "../../rust_log/src/staticlib.h"
#include "../../rust_log/src/cdylib.h"

int main() {
  staticlib();
  cdylib();
  return 0;
}