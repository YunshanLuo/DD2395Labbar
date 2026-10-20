#include <stdio.h>
#include <string.h>
#define DEBUG 1

// PS. NEVER use gets() in real code.
char * gets ( char * str );

char * pwd = "pwd0";
FILE * f;

#define DEBUG 1

int process(char * fname) {
  int length;
  char content[12];
  f = fopen(fname, "r");
  fscanf(f, "%d\n", &length);
  fread(content, length, 1, f);
  printf("%s\n", content);
  fclose(f);
  return 0;
}

int main(int argc, char ** argv) {
  char name[128];

  #ifdef DEBUG
  fprintf(stderr, "%p\n", main);
  #endif

  printf("filename? \n");
  gets(name);
  process(name);
  printf("End\n");
  return 0;
}
