all: conduit.so

FLUX_CORE_LIBS = $(shell pkg-config --libs flux-core)
FLUX_CORE_INCLUDES = $(shell pkg-config --cflags flux-core)

conduit.so: conduit.o
	gcc -Wl,--no-undefined --disable-static -shared -export-dynamic $^ -o $@ $(FLUX_CORE_LIBS)

conduit.o: conduit.c
	gcc $(FLUX_CORE_INCLUDES) $^ -fPIC -c -o $@

clean:
	rm *.o *.so
