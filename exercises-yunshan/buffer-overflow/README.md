# Lab on Buffer overflow

**IMPORTANT.** Use the Virtual Machine image from the VM page in Canvas to
complete this lab. The success of buffer-overflow attacks are depends on
compilers, memory layouts, hardware and more. By using the VM, you ensure that
you have the correct setup for developing your buffer-overflow solution,
meaning that if your solution passes all tests in the VM, the grading server
should pass it too. If you do not use the VM, we can not guarantee that the
grading server will pass your solution even if it passes all tests
locally.

Requirements for this lab are:

- understanding of C and its memory system,
- understanding of ASLR (Address Space Layout Randomization),
- usage of GDB,
- usage of Linux shell, and
- minimal usage of python.

**All experiments should be done using the provided Dockerfile.**

There are five tasks:

- [Task 1](task1) is on buffer over-read, the solution should be in `solution1.txt`.
- [Task 2](task2) is on buffer overflow, the solution should be in `solution2.txt`.
- [Task 3](task3) is on control flow hijacking, the solution should be in `solution3.py`.
- [Task 4](task4) is on code injection, the solution should be in `solution4.py`.
- [Task 5](task5) **(optional for bonus)** is on control flow hijacking and disassembly, the solution should be in `solution5.py`.
- [Task 6](task6) **(optional for bonus)** is on ROP, the solution should be in `solution6.py`.
- [Task 7](task7) **(optional for bonus)** is on ROP, the solution should be in `solution7.py`.

**Note that due to ASLR, some tests may fail even with a correct solution. Thus, you may want to rerun a failing test 2-3 times.**

# GDB Tutorial

*Note: This tutorial is made for a 64-bit VM, where the memory addresses and
pointers are 8 byte long.*

To complete the exercises you must use a debugger or a disassembler to inspect
the code produced by the compiler and find out the memory layout of the
application. Note that the virtual machine utilizes ASLR, so the base addresses
of the stack, text and data sections will be randomized for each execution.
Here we summarize some basic commands of GDB that are useful to complete your
exercises.

The directory `tutorial` contains a small program to demonstrate the usage of
GDB. Move in the directory `tutorial` and compile the example program.

```bash
cd tutorial
make
```

Explain what the program does

Run the program

```bash
./main <username>
<enter a random password>
```

To debug the program with gdb,

```bash
gdb main.elf
```

## Breakpoints, running, stepping, resuming

To stop the program just before `strcpy(local_var, username);` is executed (notice that the `strcpy` is at line 11 of main.c) set a breakpoint at line 11:

```gdb
b main.c:11
```

All Makefiles in this lab compile programs with debug symbols, which allows to set breakpoints by specifying the source code line.

To start the execution of the program, just type

```gdb
run
```

When the program terminates, you can re-execute it using `run`.  To provide the command line arguments to the program, use

```gdb
run <args>
```

When the program stops due to a breakpoint, gdb prints the status of the program

```gdb
(gdb) run roberto
Starting program: /home/student/Downloads/exercises/exercises/tutorial/main.elf roberto

Breakpoint 1, afunction (username=0x7fffffffe2e9 "roberto") at main.c:11
11	  strcpy(local_var, username);
```

In this case the Breakpoint 1 has been activated, the program has been suspended before the string copy, inside function `afunction` at line 11.  The string `roberto` has been allocated at  `0x7fffffffe2e9`, therefore the actual parameter of the function is the pointer `0x7fffffffe2e9`.  (**Notice that stack addresses can be different, due to different processes executed by linux**) A single C instruction can be executed by firing the command `next`

```gdb
(gdb) next
12	  scanf("%s", global_var);
```

GDB prints the line number and the code of the next instruction.  The program can be resumed using `continue` and restarted using `run`.  Finally, the content of a file can be redirected to the program standard input using
`run < <filename>`, e.g.

```gdb
run roberto < pwd.txt
```

## Inspecting memory
Debug the program with `gdb`, set a breakpoint at line 11 of `main.c`, start the program providing the command line argument:

```bash
~/lab-o/buffer/exercise0$ gdb main.elf

GNU gdb (Ubuntu 9.2-0ubuntu1~20.04) 9.2
Copyright (C) 2020 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from main.elf...

(gdb) b main.c:11
Breakpoint 1 at 0x11e8: file main.c, line 11.

(gdb) run roberto
Starting program: /home/student/lab-o/exercise0/main roberto

Breakpoint 1, afunction (username=0x7fffffffe2e9 "roberto") at main.c:11
11	  strcpy(local_var, username);
```

GDB provides several functions to inspect the content of memory, variables, and expressions. For instance:

```gdb
(gdb) p 16
$4 = 16
(gdb) p 0x10
$5 = 16
(gdb) p (0x10-10)
$6 = 6
```

The following command inspects the actual parameter `username` of `afunction`:

```gdb
(gdb) p username
$7 = 0x7fffffffe2e9 "roberto"
```

The actual parameter is a pointer to the address `0x7fffffffe2e9`, which contains the string `roberto\0`.

The following command prints the address where `username` is stored:

```gdb
(gdb) p &username
$8 = (char **) 0x7fffffffde08
```

The following command inspects the local variable `local_var` of `afunction`.

```gdb
(gdb) p &local_var
$11 = (char (*)[16]) 0x7fffffffde10
(gdb) p local_var
$12 = "6\336\377\377\377\177\000\000\335RUUUU\000"
```

The local variable  is allocated on the stack at `0x7fffffffde10`, it is a buffer of 16 chars, it has not been initialized, so its content contain random values.

Notice that we cannot access to local variables and parameters of other functions, since the execution is currently suspended inside `afunction`:

```gdb
(gdb) p &argc
No symbol "argc" in current context.
```

However, we can access the global variables.

```gdb
(gdb) p &global_var
$13 = (char (*)[16]) 0x555555558020 <global_var>
(gdb) p global_var
$14 = '\000' <repeats 15 times>
```

You can inspect the content of a specific region of memory.  For example, since we know that `username` is allocated in `0x7fffffffde08` we can directly inspect this memory address (** change to username, and show that the address is &username

x/a is used to print bytes as pointers
** )

```gdb
(gdb) p username
$16 = 0x7fffffffe2e9 "roberto"
(gdb) p &username
0x7fffffffde08
(gdb) x/a 0x7fffffffde08
0x7fffffffde08:	0x7fffffffe2e9
```

We are using a 64-bit machine, so pointers are 8 bytes.

(eight bytes) Before and after the variable `username` there is something else.
(it's not important what, we want just demonstrate that you can read arbitrary
addresses in memory)

```gdb
(gdb) x/a (0x7fffffffde08-8)
0x7fffffffde00:	0xc2
(gdb) x/a (0x7fffffffde08+8)
x7fffffffde10:	0x7fffffffde36
```

Additionally to variables, you can print the addresses of functions (and if you want their binary code)

```gdb
(gdb) p &afunction
$17 = (void (*)(char *)) 0x5555555551c9 <afunction>
(gdb) p &main
$18 = (int (*)(int, char **)) 0x555555555249 <main>
(gdb) x 0x555555555249
0x555555555249 <main>:	0xe5894855fa1e0ff3
```

## Changing memory content

Debug the program with gdb, set a breakpoint at line 11 of `main.c`, start the
program providing the command line argument:

```gdb
~/lab-o/exercise0$ gdb main.elf
...

(gdb) b main.c:11
Breakpoint 1 at 0x11e8: file main.c, line 11.

(gdb) run roberto
Starting program: /home/student/lab-o/exercise0/main roberto

Breakpoint 1, afunction (username=0x7fffffffe2e9 "roberto") at main.c:11
11	  strcpy(local_var, username);
```

Execute the string copy

```gdb
(gdb) next
12	  scanf("%s", global_var);
```

Print the value of `local_var`

```gdb
(gdb) p local_var
$19 = "roberto\000\335RUUUU\000"
```

You can change the second character of `local_var` by directly writing
into the memory. ** Warning the address 0xbffff09c can be different **

```gdb
(gdb) p local_var
$19 = "roberto\000\335RUUUU\000"
(gdb) p &local_var
$20 = (char (*)[16]) 0x7fffffffde10
(gdb) set *((char *)(0x7fffffffde10 + 1)) = 'X'
(gdb) p local_var
$21 = "rXberto\000\335RUUUU\000"
```

You must specify the data type, for example if you set a pointer (void *) then 8 bytes are changed:

```gdb
(gdb) set *((void **)(0x7fffffffde10 + 1)) = 0
(gdb) p local_var
$22 =  "r\000\000\000\000\000\000\000\000RUUUU\000"
```

## Inspecting the stack

Debug the program with gdb, set a breakpoint at line 11 of `main.c`, start the program providing the command line argument:

```bash
~/lab-o/exercise0$ gdb main.elf
...

(gdb) b main.c:11
Breakpoint 1 at 0x11e8: file main.c, line 11.

(gdb) run roberto
Starting program: /home/student/lab-o/exercise0/main roberto

Breakpoint 1, afunction (username=0x7fffffffe2e9 "roberto") at main.c:11
11	  strcpy(local_var, username);
```

The stack of frames can be inspected using the command `bt`

```gdb
(gdb) bt
#0  afunction (username=0x7fffffffe2e9 "roberto") at main.c:11
#1  0x0000555555555288 in main (argc=2, argv=0x7fffffffdf48) at main.c:24
```

Here the stack contains two frames, the top (and active) frame #0 (actually in lower memory address) is for the function `afunction`, while the bottom frame #1 (actually in a higher memory address) is for the function `main`, which is also the entry point of the program.  The funciton `main` has been invoked with two parameters: `argc=2` and `argv=0x7fffffffdf48`. The latter is a pointer to an array of strings allocated by the OS and containing the command line arguments.  The function `afunction` has been invoked with one parameter: `username=0x7fffffffe2e9`. This is the address of a string containing `roberto\0`.

The active frame can be inspected using `info f`

```gdb
(gdb) info f
Stack level 0, frame at 0x7fffffffde40:
 rip = 0x5555555551e8 in afunction (main.c:11); saved rip = 0x555555555288
 called by frame at 0x7fffffffde60
 source language c.
 Arglist at 0x7fffffffddf8, args: username=0x7fffffffe2e9 "roberto"
 Locals at 0x7fffffffddf8, Previous frame's sp is 0x7fffffffde40
 Saved registers:
  rbp at 0x7fffffffde30, rip at 0x7fffffffde38
```

The active frame (i.e. the one for `afunction`) ends at address `0x7fffffffde40`.  Inside the frame (i.e. below its end-address) there are (in order):

- parameters (i.e. `username`)
- local variables (i.e. `local_var`)
- the address where the previous frame started (at address `0x7fffffffde40-16`)
- the `saved rip` (at address `0x7fffffffde40-8`)

```gdb
p &username
$25 = (char **) 0x7fffffffde08
(gdb) p &local_var
$24 = (char (*)[16]) 0x7fffffffde10
(gdb) x/a (0x7fffffffde40-16)
0x7fffffffde30:	0x7fffffffde50
(gdb) x/a (0x7fffffffde40-8)
0x7fffffffde38:	0x555555555288 <main+63>
```

The `saved rip` is the return address, which is the address where the funciton
should jump back after termination. In this case, the invocation of `afunction`
should jump back to the address `0x555555555288`.  Information about the code
located at this address is obtained as follows:

```gdb
(gdb) info line *0x555555555288
Line 25 of "main.c" starts at address 0x555555555288 <main+63> and ends at
0x55555555528d <main+68>
```

This address corresponds to line 25 of `main`: the line that immediately
follows the invocation of `afunction`.

## Disassembly

Debug the program with gdb and dissassembly the `main` function:

```bash
~/lab-o/exercise0$ gdb main.elf
...
   0x0000000000001249 <+0>:	endbr64
   0x000000000000124d <+4>:	push   %rbp
   0x000000000000124e <+5>:	mov    %rsp,%rbp
   0x0000000000001251 <+8>:	sub    $0x10,%rsp
   0x0000000000001255 <+12>:	mov    %edi,-0x4(%rbp)
   0x0000000000001258 <+15>:	mov    %rsi,-0x10(%rbp)
   0x000000000000125c <+19>:	cmpl   $0x1,-0x4(%rbp)
   0x0000000000001260 <+23>:	jg     0x1275 <main+44>
   0x0000000000001262 <+25>:	lea    0xdbf(%rip),%rdi        # 0x2028
   0x0000000000001269 <+32>:	callq  0x10a0 <puts@plt>
   0x000000000000126e <+37>:	mov    $0x0,%eax
   0x0000000000001273 <+42>:	jmp    0x128d <main+68>
   0x0000000000001275 <+44>:	mov    -0x10(%rbp),%rax
   0x0000000000001279 <+48>:	add    $0x8,%rax
   0x000000000000127d <+52>:	mov    (%rax),%rax
   0x0000000000001280 <+55>:	mov    %rax,%rdi
   0x0000000000001283 <+58>:	callq  0x11c9 <afunction>
   0x0000000000001288 <+63>:	mov    $0x0,%eax
   0x000000000000128d <+68>:	leaveq
   0x000000000000128e <+69>:	retq
```

The code corresponding to `printf("Use ./main <username>\n<input password>\n")`
is the following

```text
   0x0000000000001262 <+25>:	lea    0xdbf(%rip),%rdi        # 0x2028
   0x0000000000001269 <+32>:	callq  0x10a0 <puts@plt>
```

The first instruction `lea    0xdbf(%rip),%rdi`, saves into register `rdi` the
value of the next program counter plus constant `0xdbf`: i.e.,

```gdb
gdb) x/a (0xdbf + 0x0000000000001269)
0x2028
```

The compilers as allocated the constant string `"Use ./main <username>\n<input
password>\n"` in that address of the program

```gdb
(gdb) x/s (0x2028)
0x2028:	"Use ./main <username>\n<input password>"
```

The second instruction: `callq  0x10a0 <puts@plt>` calls `puts` (i.e., `printf`
when there is only one parameter.)
Notice that `puts` has been linked at the
address `0x10a0` and that it expects the address of the string to print in the
register `rdi`.

```gdb
(gdb) x/a &puts
0x10a0 <puts@plt>
```

## References

Look at [GDB Manual](https://sourceware.org/gdb/current/onlinedocs/gdb/) for more detailed information on GDB.
