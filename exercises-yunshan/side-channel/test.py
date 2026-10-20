#!/usr/bin/env python3

from crypto import *
import attack

import unittest
import random

class test(unittest.TestCase):
    def execute_attack(self, plaintext, key):
        m = Cache()
        m.clean()
        c = Crypto()
        msg = c.feistel_encrypt(m, plaintext, key)
        (b1, b2) = attack.infer_plaintext(msg, m)
        self.assertIn(plaintext[0], b1)
        self.assertIn(plaintext[1], b2)
        self.assertLess(len(b1), 17)
        self.assertLess(len(b2), 17)
        return

    def test1(self):
        self.execute_attack("ab", "12")
    def test2(self):
        self.execute_attack("cd", "12")
    def test3(self):
        self.execute_attack("cd", "49")

if __name__ == '__main__':
    unittest.main()
