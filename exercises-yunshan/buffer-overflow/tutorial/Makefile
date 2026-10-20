.PHONY: all clean

CC=gcc
CFLAGS=-O0 -ggdb

all: main.elf

clean:
	rm -f main.elf

main.elf: main.c
	$(CC) -o $@ $< $(CFLAGS)
