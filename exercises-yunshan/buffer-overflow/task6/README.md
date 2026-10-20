# Task 6

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

## Problem 6.1

Forge a file that makes the application leak the password and email that are stored
internally.
Since you probably need a file that contains "special" bytes, use the
following procedure:

1. complete the python script `solution6.py`, which reads the memory location of
   main, write the forged content in a file, and then writes the name the file
   to the standard output
2. execute `./solution6.py < my.pipe | ./main.elf 2>my.pipe` which feeds your
   `solution6.py` with the `main.elf` standard error output, and feeds
   `main.elf` with the standard output of `solution6.py`.

The target `attack` of the Makefile automates tasks 2, so you only need to execute `make attack` for step 2.  Your solution consists of the script `solution6.py`.

To test your solution execute `./test.py`.

## Hints

Differently from Task 3, you should chain both functions that print password and
email.
Therefore you can use a ROP attack and chain two gadgets: first a gadget inside
``printEmail`` that prints the email, and then a gadget inside ``printPwd`` that
prints the password. Notice that it is not enough to jump to the call to
``puts``. Instead your attack should point to the instructions that prepare the
parameters for ``puts``.
These can be found by disassembling the two functions.

Debug the program using GDB and find the distance between the location of
1. the variable `content` and `saved rip`, and
2. the function `printEmail` and the invocation of `puts`.
3. the function `printPwd` and the invocation of `pwd`.

Do not worry if the program crashes after leaking the email and password.
