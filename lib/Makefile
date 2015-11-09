prefix = /usr
CC=gcc
CFLAGS=-I.
LIBS += -lcomedi -lm -lreadline
#LIBS += -lefence



aad: $()
	$(CC) -c -o aad.c $(LIBS)

clean:
	-rm -f aad *.o