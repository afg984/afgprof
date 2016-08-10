#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/sendfile.h>
#include <stdlib.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>


FILE* file;

void _mcleanup() {
    fclose(file);
}

void monstartup() {
    pid_t pid = getpid();
    char filename[80];
    sprintf(filename, "/data/gmon/%d", pid);
    mkdir(filename, 0755);
    sprintf(filename, "/data/gmon/%d/maps", pid);
    file = fopen(filename, "w");
    int mfd = open("/proc/self/maps", O_RDONLY);
    sendfile(fileno(file), mfd, 0, SIZE_MAX);
    close(mfd);
    fclose(file);
    sprintf(filename, "/data/gmon/%d/unmapped-calls", pid);
    file = fopen(filename, "w");
    atexit(_mcleanup);
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
