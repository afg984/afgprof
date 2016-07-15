#include <stdio.h>
#include <stdlib.h>


void _mcleanup() {
    puts("=== _mcleanup() invoked ===");
}

void monstartup() {
    puts("=== start of monstartup() ===");
    FILE* file = fopen("/proc/self/maps", "r");
    char buf[80];
    if (file) {
        int n;
        while (0 != (n = fread(buf, 1, sizeof(buf), file))) {
            fwrite(buf, 1, n, stdout);
            if (n != sizeof(buf)) break;
        }
    }
    atexit(_mcleanup);
    puts("=== end of monstartup() ===");
}

void __mcount_internal(u_long caller_lr, u_long caller_pc) {
    static int called = 0;
    if (!called) {
        monstartup();
    }
    called = 1;
    printf("LR = %x ; PC = %x\n", caller_lr, caller_pc);
}
