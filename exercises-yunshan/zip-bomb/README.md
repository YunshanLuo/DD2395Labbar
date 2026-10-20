# Introduction

A zip bomb (also known as a compression bomb) uses compression techniques to create a small file that, when uncompressed, expands to a significantly larger size. This can overwhelm system resources, potentially causing instability, crashes, or denial of service (DoS).
Zip bombs can lead to resource exhaustion in a system in various ways:
* **CPU and memory overload:** To handle the decompression process, the system must allocate significant CPU and memory resources, which can lead to system overload.
* **Denial of Service (DoS):** A zip bomb can target a network or server infrastructure, consuming available bandwidth and causing disruption.

There are two main types of zip bombs: recursive and non-recursive. Recursive zip bombs work by nesting multiple zip files inside each other, where each file unzips into another. The most famous example is the file *42.zip* (42 KB to 4.5 PB). However, most modern unzip tools do not decompress files recursively. The second type, non-recursive zip bombs, achieve high compression ratios by using overlapping files within a single zip file.

In this lab, you will first implement a [non-recursive zip
 bomb](https://www.bamsoftware.com/hacks/zipbomb/).
Reference to the zip file format can be found [here](https://pkware.cachefly.net/webdocs/APPNOTE/APPNOTE-6.3.10.TXT)

Lab consists of one small tutorial and three tasks:
- [Tutorial](tutorial): shows how to use the supplied helping functions to create a simple zip file
- [Task 1](task1): creates a zip bomb by sharing data among multiple files
- [Task 2](task2): creates a zip bomb by overlapping data
- [Task 3](task3): creates a zip bomb detector that scans zip files for characteristics of non-recursive zip bombs, evaluating the file structure to identify potential threats.

## Verifying solutions

[`safe_unzip.py`](unzip/safe_unzip.py) can and should be used to verify all zip
files as part of tasks in this lab.
It unzips the file without writing it anywhere, and checks the compression rate of the file (``uncompressed_size/compressed_size``). Please follow the instructions in the [`unzip/README.md`](unzip/README.md) file when verifying any zip file in this lab.

## Contributions

This lab has been created as a project of course DD2391 by
Birger Karlsson,
Mathias Grindsäter,
Melvin Sandberg, and
Oskar Vesterlund.
