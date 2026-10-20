.PHONY: all attack clean test

CC=gcc
CFLAGS= -fno-stack-protector -z execstack -O0 -ggdb

all: test

test:
	./test.py

clean:
	rm -f main.elf shell.bin my.fifo

attack: main.elf shell.bin my.fifo
	./solution4.py < my.fifo | ./main.elf 2>my.fifo

main.elf: main.c
	$(CC) -o $@ $< $(CFLAGS)

shell.bin: shell.asm
	nasm -f bin -o $@ $<

my.fifo:
	[ -p $@ ] || mkfifo $@
