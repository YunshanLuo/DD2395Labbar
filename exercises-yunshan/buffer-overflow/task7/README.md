# Task 7

The application receives a file name from the standard input and parses the
file. The file format consists of two lines: the first line indicates the number
of characters of the content, which starts from the second line. For example:

```shell
# Compile the program
$ make

let a.txt contain
6
hello\0

$ ./main.elf
0x56ff2531280
filename?
a.txt
hello
End
```

Look at the source code, notice that the developer has forgotten to turn off
the `DEBUG` flag, causing the program to leak the location of the main
function to standard error. Also, notice that the location of the main function
changes on every execution due to ASLR.

## Problem 7.1

Forge a file that makes the application leak the password that is stored
internally.
Since you probably need a file that contains "special" bytes, use the
following procedure:

1. complete the python script `solution7.py`, which reads the memory location of
   main, write the forged content in a file, and then writes the name the file
   to the standard output
2. execute `./solution7.py < my.pipe | ./main.elf 2>my.pipe` which feeds your
   `solution7.py` with the `main.elf` standard error output, and feeds
   `main.elf` with the standard output of `solution5.py`.

The target `attack` of the Makefile automates tasks 2, so you only need to execute `make attack` for step 2.  Your solution consists of the script `solution7.py`.

To test your solution execute `./test.py`.

## Hints

Differently from Task 3, there is no function that directly prints the
password. Therefore you can use a ROP attack and chain two gadgets: first one the sets
the parameters for ``printf`` (or ``puts``) to point to the password, the second
one that invokes ``printf`` (or ``puts``).

We suggest to use a gadget that invokes ``puts``, since ``printf``
uses varargs and preparing its parameters is more complicated. In case of
``puts`` the parameter is passed via register ``rdi``.
If you disassemble ``main`` you can notice that several invocations of``printf`` have been
actually compiled as invocation of ``puts``.

Debug the program using GDB and find the distance between the location of
1. the variable `content` and `saved rip`, and
2. the function `main` and one invocation of `puts`.
3. the function `main` and the location of `pwd`.

To find a gadget that sets ``rdi`` you can use

```shell
r2 main.elf
> /R pop rdi
```

Do not worry if the program crashes after leaking the password.
