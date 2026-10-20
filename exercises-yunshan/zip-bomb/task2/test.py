#!/usr/bin/env python3

import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unzip.safe_unzip import *
from solution import *

class test(unittest.TestCase):
    def test(self):
        create_zip_bomb(25)
        (compressed, decompressed) = compute_size("zip_bomb_2.zip")
        self.assertTrue(decompressed/compressed > 10000)
        content = extract_content("zip_bomb_2.zip", "file1.txt")
        self.assertTrue(content.decode('utf-8') == "A"*10000000)

if __name__ == '__main__':
    unittest.main()
