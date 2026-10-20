#!/bin/bash

ROOT=$(realpath $(dirname $0))

TESTS="""
buffer-overflow/task1
buffer-overflow/task2
buffer-overflow/task3
buffer-overflow/task4
buffer-overflow/task5
buffer-overflow/task6
buffer-overflow/task7
dos
hash
malware
side-channel
zip-bomb/task1
zip-bomb/task2
zip-bomb/task3
"""

for test in $TESTS; do
	cd $ROOT/$test
	if ./test.py 2>/dev/null 1>&2; then
		printf "$test PASS\n"
	else
		printf "$test FAIL\n"
	fi
done
