#!/usr/bin/env python3
from insecure_hash import hash_string
from Cryptodome.Cipher import AES


def find_collision(message):
    # Your solution
    hashed_message = hash_string(message)
    key = b"." * 16
    cipher = AES.new(key, mode=AES.MODE_ECB)
    block = cipher.encrypt(hashed_message)
    return block + key

if __name__ == '__main__':
    message = b"aaaaaaaaaaaaaaaabbbbbbbbbbbbbbbb"
    print("Hash of %s is %s" % (message, hash_string(message)))
    collision = find_collision(message)
    print("Hash of %s is %s" % (collision, hash_string(collision)))
