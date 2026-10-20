#!/usr/bin/env python3
import unittest
from solution import *

class test(unittest.TestCase):
    def test(self):
        self.assertFalse(is_zip_bomb("zip_file.zip"))
        self.assertTrue(is_zip_bomb("zip_bomb.zip"))

if __name__ == '__main__':
    unittest.main()
