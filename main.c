#include "shared.h"

void a() {
    shared_function();
}


void b() {
    a();
}


void c() {
    a();
    b();
}


int main() {
    a();
    b();
    c();
}
