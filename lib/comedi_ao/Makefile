
prefix = /usr

CFLAGS += -Wall -Wstrict-prototypes -O2 -g
CFLAGS += `pkg-config --cflags glib-2.0`
CFLAGS += `pkg-config --cflags plplotd`
CFLAGS += -DNI625x

LIBS += -lcomedi -lm -lreadline
LIBS += `pkg-config --libs glib-2.0`
LIBS += `pkg-config --libs plplotd`
#LIBS += -lefence
#LDFLAGS += -static

krank_objs = ao_slave.o

multikrank: $(krank_objs)
	$(CC) $(LDFLAGS) -o ao_slave $(krank_objs) $(LIBS)

clean:
	-rm -f ao_slave

