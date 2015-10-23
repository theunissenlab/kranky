
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

install:
	install -d $(prefix)/bin/
	install -m755 multikrank $(prefix)/bin/
	install -d $(prefix)/share/doc/doupelab-krank/examples/
	install -m644 scope.rc $(prefix)/share/doc/doupelab-krank/examples/
	install -m644 setup.rc $(prefix)/share/doc/doupelab-krank/examples/
	install -d $(prefix)/share/doc/doupelab-krank/examples/songs
	install -m644 songs/*.bin $(prefix)/share/doc/doupelab-krank/examples/songs

