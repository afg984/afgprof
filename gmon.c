#include <stdio.h>
#include <stdlib.h>


FILE* output;

void _mcleanup() {
    fputs("=== _mcleanup() invoked ===\n", output);
    fclose(output);
}

void monstartup() {
    output = fopen("/data/gmon.out.txt", "w");
    fputs("=== start of monstartup() ===\n", output);
    FILE* file = fopen("/proc/self/maps", "r");
    char buf[80];
    if (file) {
        int n;
        while (0 != (n = fread(buf, 1, sizeof(buf), file))) {
            fwrite(buf, 1, n, output);
            if (n != sizeof(buf)) break;
        }
    }
    atexit(_mcleanup);
    fputs("=== end of monstartup() ===\n", output);
}

void __mcount_internal(u_long caller_lr, u_long caller_pc) {
    static int called = 0;
    if (!called) {
        monstartup();
    }
    called = 1;
    fprintf(output, "LR = %x ; PC = %x\n", caller_lr, caller_pc);
}
