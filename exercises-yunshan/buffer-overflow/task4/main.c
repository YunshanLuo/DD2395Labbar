/* #pragma GCC diagnostic ignored "-Wdeprecated-declarations" */
#include <stdio.h>
#include <pthread.h>
#define DEBUG 1

// PS. NEVER use gets in real code.
char * gets ( char * str );


void get_mail() {
  char mail_subject[32];
  char mail_body[128];

#ifdef DEBUG
  fprintf(stderr, "%p\n", &mail_subject);
#endif

  // Get email subject and body
  printf("Enter the mail subject:\n");
  gets(mail_subject);

  printf("Enter the mail body:\n");
  gets(mail_body);
}

int main(int argc, char** argv) {
  get_mail();
  printf("Sending the email\n");
}
