#!/usr/bin/env python3
import math
from Cryptodome.Cipher import AES


def hash_string(message):
    """ Compute the hash of message.

    if message = B1;B2;B3;...Bn and Bi are blocks of 128 bits
    computers DEC(....DEC(DEC(B1, B2), B3)...), Bn)
    where DEC is AES decryption
    """
    block = message[:16]
    # pad first block
    block = block + b" " * (16-len(block))
    for i in range(1, max(2, int(math.ceil(len(message)/16.0)))):
        # extract the i-th block
        key = message[i*16:i*16+16]
        # pad the i-th block
        key = key + (b" " * (16-len(key)))
        cipher = AES.new(key, mode=AES.MODE_ECB)
        block = cipher.decrypt(block)
    return block


if __name__ == '__main__':
    print (hash_string(b"aaaaaaaaaaaaaaaabbbbbbbbbbbbbbbb"))
    print (hash_string(b"bbbbbbbbbbbbbbbbaaaaaaaaaaaaaaaa"))
    print (hash_string(b"0123456789abcdefhello"))
