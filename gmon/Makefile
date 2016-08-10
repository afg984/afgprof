TOOLCHAIN = arm-linux-androideabi-
CC = $(TOOLCHAIN)gcc -O3
CFLAGS = -pie -march=armv7-a -Wall -Wextra
AR = $(TOOLCHAIN)ar

a.out: main.c gmon.a libshared.so
	$(CC) $(CFLAGS) -g -pg $^ -L. -lshared

libshared.so: shared.c
	$(CC) $(CFLAGS) -pg -shared $^ -o $@

.PHONY: clean
clean:
	rm -f $(wildcard *.a *.o a.out gprof.out.txt)

mcount.o: mcount.s
	$(CC) $(CFLAGS) -c $^

gmon.o: gmon.c
	$(CC) $(CFLAGS) -c $^

gmon.a: gmon.o mcount.o
	$(AR) r $@ $^

.PHONY: profile
profile: a.out libshared.so
	adb root
	adb shell rm -rf /data/gmon
	adb shell mkdir /data/gmon
	adb shell chmod 777 /data/gmon
	adb push a.out /data
	adb push libshared.so /data
	adb shell "time LD_LIBRARY_PATH=/data /data/a.out"
	adb pull /data/gmon gmon
