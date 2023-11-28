#include <iostream>
using namespace std;

long fact(int);

long fact(int ip) {
    if (ip == 1) {
        return 1;
    }
    else {
        return ip * fact(ip - 1);
    }
}
