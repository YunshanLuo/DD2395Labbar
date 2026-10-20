# README

In this repository, we have resources for the following:
- [Lab O (buffer-overflow)](buffer-overflow): Develop buffer-overflow attacks targeting vulnerable applications.
- [Denial of Service](dos): Develop a filter for preventing Denial-of-Service attack on a simple compression algorithm.
- [(In)secure hash function](hash): Develop a function that given a plaintext, find another plaintext whose hashes collides.
- [Malware](malware): Develop a simple antivirus program.
- [Side channels](side-channel): Develop a side-channel attack against an encryption algorithm.
- [Lab Z (zip-bomb)](zip-bomb): Develop zip bombs that can cause denial
  of service and implement a detector for this type of zip files (optional lab
  and alternative to the optional tasks of Lab W or the optional tasks of lab O).

These assignments uses an automatic grading system.
To submit your solutions to the grading system, simply make a commit and push.

```bash
git add [my solution file]
git commit -m"Adds my solution to foobar"
git push
```

Feedback from the grading system will appear as a comment on your commit on GitS.

The locations of the solutions files for the exercises and lab O are *hardcoded*.
If they are moved, the automatic grading system will not be able to test your solutions.

You have to write your solution in the provided files, you are not allowed to
add new files to the exercises.

Solution files:
- `buffer-overflow/task1/solution1.txt`
- `buffer-overflow/task2/solution2.txt`
- `buffer-overflow/task3/solution3.py`
- `buffer-overflow/task4/solution4.py`
- `buffer-overflow/task5/solution5.py`
- `buffer-overflow/task6/solution6.py`
- `buffer-overflow/task7/solution7.py`
- `dos/filter.py`
- `hash/collision.py`
- `malware/antivirus.py`
- `side-channel/attack.py`
- `zip-bomb/task1/solution.py`
- `zip-bomb/task2/solution.py`
- `zip-bomb/task3/solution.py`

## Using Docker

To use the container in this repository, build an image using the included
Dockerfile (if you use "rootfull" docker, you may need to use sudo docker):

```bash
# Build image called `compsec`, note the "." at the end is part of the command
docker build -t compsec .
```

Now test run the exercises as follows:

```bash
# Creates a new ephemeral container from `student` and run the ./test.sh file to test all solutions at once.
# This will create a container from the `compsec` image where the current directory `.` is mounted at `/workdir`.
docker run -it --rm -v .:/workdir -w /workdir compsec ./test.sh

# Or you can go to a specific exercise and run a test
cd dos
docker run -it --rm -v .:/workdir -w /workdir compsec ./test.py

# And get an interactive shell in the container by removing `./test.py`.
docker run -it --rm -v .:/workdir -w /workdir compsec
root@deadbeef:/workdir $ ./test.sh
root@deadbeef:/workdir $ exit
```
