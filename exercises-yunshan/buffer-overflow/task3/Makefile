.PHONY: all attack clean test

CC=gcc
CFLAGS=-O0 -ggdb -fno-stack-protector

all: test

test:
	./test.py

clean:
	rm -f main.elf my.fifo

attack: main.elf my.fifo
	./solution3.py < my.fifo | ./main.elf 2>my.fifo

my.fifo:
	[ -p $@ ] || mkfifo $@

main.elf: main.c
	$(CC) -o $@ $< $(CFLAGS)
