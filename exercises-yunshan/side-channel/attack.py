#!/usr/bin/env python3

import itertools
import crypto

def infer_plaintext(msg, m):
    # Example on probing cache lines
    (_, t) = m.read_address(0 * crypto.cache_line_size)
    if (t == 1):
        print("Cache line 0 has been accessed")
    (_, t) = m.read_address(1 * crypto.cache_line_size)
    if (t == 1):
        print("Cache line 1 has been accessed")
    # Your solution
    possible_values = set(map(chr, range(256)))
    return (possible_values, possible_values)
