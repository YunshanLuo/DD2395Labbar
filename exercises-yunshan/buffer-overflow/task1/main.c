#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char ** argv) {
  char pwd[8];
  char name[8];
  int i,n = 0;

  if (argc < 3) {
    printf("Use ./main <user> <chars-to-echo>\n");
    return 1;
  }

  strcpy(pwd, "pwd0");
  strcpy(name, argv[1]);
  n = atoi(argv[2]);
  write(1, name, n);
  write(1, "\n", 1);
  return 0;
}
