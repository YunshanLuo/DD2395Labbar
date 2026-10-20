# Task 5

The application receives two values from the standard input (both terminated by
a newline): (1) name and (2) password.

For example:

```shell
# Compile the program
$ make

$ ./main.elf
0x56ff2531280
Start
Name?
student
Password?
time2work
Hello student
non authorized
End

$ ./main.elf
0x55ff2198280
Start
Name?
student
Password?
pwd0
Hello student
authorized
End

$ ./main.elf hello pwd0
0x55b00654c280
Start
Name?
hello
Password?
pwd0
Hello hello
authorized
End
```

Look at the source code, notice that the developer has forgotten to turn off
the `DEBUG` flag, causing the program to leak the location of the main
function to standard error. Also, notice that the location of the main function
changes on every execution due to ASLR.

## Problem 5.1

Forge a username that makes the application leak the password that is stored
internally.

Since you probably need a username that contains "special" bytes, use the
following procedure:

1. complete the python script `solution5.py`, which reads the memory location
   of main and then prints the forged output on the standard output
2. execute `./solution5.py < my.pipe | ./main.elf 2>my.pipe` which feeds your
   `solution5.py` with the `main.elf` standard error output, and feeds
   `main.elf` with the standard output of `solution5.py`.

The target `attack` of the Makefile automates tasks 2, so you only need to execute `make attack` for step 2.  Your solution consists of the script `solution5.py`.

To test your solution execute `./test.py`.

## Hints

By disassembly the program you can notice that `puts(pwd)` has been
implemented by the instructions:

```assembly
   0x000000000000124e <+101>:	mov    0x2dbb(%rip),%rax        # 0x4010 <pwd>
   0x0000000000001255 <+108>:	mov    %rax,%rdi
   0x0000000000001258 <+111>:	callq  0x10b0 <puts@plt>
```
The instruction `mov    0x2dbb(%rip),%rax`: (1) adds 0x2dbb to the next program
counter, obtaining the value 0x2008. This value is the address of the global
variable `pwd`. This variable points to a location in memory that is where the
password is stored. (2) It loads from the variable `pwd` the address of the
constant password.

```assembly
(gdb) x/a 0x0000000000001255+0x2dbb
0x4010 <pwd>:	0x2008
(gdb) x/s 0x2008
0x2008:	"pwd0"
```

The second instruction copies the value of `eax` to `rdi` and the last
instruction invokes the `puts` function.
Notice that `puts` has been linked at the
address `0x10b0` and that it expects the address of the string to print in the
register `rdi`.


To find all possible invocations of `puts` you can also use

```shell
r2 main.elf
> /R call 0x10b0
```
