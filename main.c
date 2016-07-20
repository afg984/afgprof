#include "shared.h"
#include <stdio.h>

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


int fib(int n) {
    if (n < 3) return 1;
    else return fib(n - 1) + fic(n - 2);
}


int fic(int n) {
    return fib(n);
}


int main() {
    a();
    b();
    c();
    int i;
    for (i = 0; i < 32; ++ i) {
        printf("fib(%d) = %d\n", i, fib(i));
    }
}
