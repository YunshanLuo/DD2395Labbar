#!/usr/bin/env python3

import unittest
import subprocess
import os

class test(unittest.TestCase):
    def test(self):
        os.system("make main.elf")
        with open("solution1.txt", "r") as f:
            values = [v for l in f.readlines() if not l.startswith("#") for v in l.split()]
        try:
            res = subprocess.check_output(f"./main.elf {' '.join(values)}", shell=True)
        except subprocess.CalledProcessError as e:
            res = ""
        print(res.decode(errors="replace"))
        self.assertTrue(b"pwd0" in res)


if __name__ == '__main__':
    unittest.main()
