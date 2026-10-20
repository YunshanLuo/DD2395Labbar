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

with open("payload.txt", "wb") as f:
    writeStr(f, "6\nhello\0")

print("payload.txt")
