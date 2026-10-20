.PHONY: all clean test

CC=gcc
CFLAGS=-O0 -ggdb -fno-stack-protector

all: test

test: main.elf
	./test.py

clean:
	rm -f main.elf

main.elf: main.c
	$(CC) -o $@ $< $(CFLAGS)
