#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/sendfile.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>


FILE* file;

void _mcleanup() {
    fputs("=== _mcleanup() invoked ===\n", file);
    fclose(file);
}

void monstartup() {
    file = fopen("/data/gmon.out.txt", "w");
    int mfd = open("/proc/self/maps", O_RDONLY);
    sendfile(fileno(file), mfd, 0, SIZE_MAX);
    close(mfd);
    atexit(_mcleanup);
    fputs("=== end of monstartup() ===\n", file);
}

void __mcount_internal(u_long caller_lr, u_long caller_pc) {
    static int called = 0;
    if (!called) {
        monstartup();
    }
    called = 1;
    fwrite(&caller_lr, 1, sizeof(u_long), file);
    fwrite(&caller_pc, 1, sizeof(u_long), file);
}
