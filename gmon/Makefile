TOOLCHAIN = arm-linux-androideabi-
COMPILER = gcc
CC = $(TOOLCHAIN)$(COMPILER)
CFLAGS = -O3 -pie -march=armv7-a -Wall -Wextra
AR = $(TOOLCHAIN)ar

a.out: main.o gmon.a libshared.so
	$(CC) $(CFLAGS) -O0 -g -pg $^ -L. -lshared

libshared.so: shared.c
	$(CC) $(CFLAGS) -pg -shared $^ -o $@

main.o: main.c
	$(CC) $(CFLAGS) -O0 -c -pg $^

.PHONY: clean
clean:
	rm -f $(wildcard *.a *.o a.out libshared.so)

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
