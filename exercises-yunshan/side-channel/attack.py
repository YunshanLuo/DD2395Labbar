#!/usr/bin/env python3

import itertools
import crypto

def infer_plaintext(msg, m):
    # which lines encryption left loaded -- snapshot before the example
    # below touches lines 0/1
    touched = []
    for line in range(crypto.cache_lines):
        if m.cache[line]["tag"] is not None:
            touched.append(line)
    # Example on probing cache lines
    (_, t) = m.read_address(0 * crypto.cache_line_size)
    if (t == 1):
        print("Cache line 0 has been accessed")
    (_, t) = m.read_address(1 * crypto.cache_line_size)
    if (t == 1):
        print("Cache line 1 has been accessed")
    # Your solution
    c0 = ord(msg[0])
    c1 = ord(msg[1])

    # each touched line spans 8 bytes of T; the round index is one of them
    indices = []
    for line in touched:
        for offset in range(crypto.cache_line_size):
            indices.append(line * crypto.cache_line_size + offset)

    # c0 = l0 ^ T[i0], c1 = r0 ^ T[i1]; can't tell which line is which round
    possible_l0 = set()
    possible_r0 = set()
    for i in indices:
        possible_l0.add(chr(c0 ^ crypto.T[i]))
        possible_r0.add(chr(c1 ^ crypto.T[i]))

    return (possible_l0, possible_r0)
