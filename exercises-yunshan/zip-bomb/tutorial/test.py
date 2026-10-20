#!/usr/bin/env python3

import unittest
# add to path the shared functions
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unzip.safe_unzip import *

from tutorial import *

class test(unittest.TestCase):
    def test(self):
        create_zip_file()
        (compressed, decompressed) = compute_size("zip_file.zip")
        self.assertTrue(decompressed == 22)
        content = extract_content("zip_file.zip", "file1.txt")
        self.assertTrue(content.decode('utf-8') == "File data to compress.")

if __name__ == '__main__':
    unittest.main()
