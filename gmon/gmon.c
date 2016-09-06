#include <endian.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/sendfile.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include "tree.h"


static FILE *file;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static volatile int term_received = 0;

struct call_count {
    union {
        struct {
            uint32_t lr;
            uint32_t pc;
        };
        uint64_t key;
    };
    uint64_t count;
    RB_ENTRY(call_count) entry;
};

static int call_count_cmp(struct call_count *a, struct call_count *b) {
    if (a->key < b->key) {
        return -1;
    } else if (a->key > b->key) {
        return 1;
    } else {
        return 0;
    }
}

RB_HEAD(call_count_head, call_count) head = RB_INITIALIZER(&head);

RB_PROTOTYPE(call_count_head, call_count, entry, call_count_cmp);
RB_GENERATE(call_count_head, call_count, entry, call_count_cmp);

static void increment(uint32_t lr, uint32_t pc) {
    struct call_count *cc = malloc(sizeof(struct call_count));
    cc->lr = lr;
    cc->pc = pc;
    struct call_count *inserted = RB_INSERT(call_count_head, &head, cc);
    if (inserted) {
        ++inserted->count;
    } else {
        cc->count = 1;
    }
}

void _mcleanup() {
    struct call_count *cc;
    RB_FOREACH(cc, call_count_head, &head) { fwrite(cc, 1, 16, file); }
    fclose(file);
}

void sighandler(int sig) {
    (void)sig;
    switch (pthread_mutex_trylock(&mutex)) {
    case 0:
        _mcleanup();
        abort();
        return;
    case EBUSY:
        term_received = 1;
        return;
    default:
        abort();
        // this shall not happen
    }
}

struct sigaction sa;

void monstartup() {
    pid_t pid = getpid();
    char filename[80];

    sprintf(filename, "/data/gmon/%d", pid);
    mkdir(filename, 0755);

    sprintf(filename, "/data/gmon/%d/maps", pid);
    int ofd = open(filename, O_WRONLY | O_CREAT);
    int mfd = open("/proc/self/maps", O_RDONLY);
    sendfile(ofd, mfd, 0, SIZE_MAX);
    close(mfd);
    close(ofd);

    sprintf(filename, "/data/gmon/%d/calls", pid);
    file = fopen(filename, "w");
    atexit(_mcleanup);

    // setup signal handler for SIGTERM
    sa.sa_handler = sighandler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGTERM, &sa, 0);
}

void __mcount_internal(u_long lr, u_long pc) {
    pthread_mutex_lock(&mutex);

    static int called = 0;

    if (!called) {
        monstartup();
        called = 1;
    }
    increment(lr, pc);

    if (term_received) {
        _mcleanup();
        abort();
    }

    pthread_mutex_unlock(&mutex);
}
