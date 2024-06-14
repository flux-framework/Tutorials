all: capp.so ioapp.so

FLUX_CORE_LIBS = $(shell pkg-config --libs flux-core)
FLUX_CORE_INCLUDES = $(shell pkg-config --cflags flux-core)

ioapp.so: ioapp.o
	gcc -Wl,--no-undefined --disable-static -shared -export-dynamic $^ -o $@ $(FLUX_CORE_LIBS)

ioapp.o: app.c 
	gcc $(FLUX_CORE_INCLUDES) $^ -DIO_SERVICE=1 -fPIC -c -o $@

capp.so: capp.o
	gcc -Wl,--no-undefined --disable-static -shared -export-dynamic $^ -o $@ $(FLUX_CORE_LIBS)

capp.o: app.c 
	gcc $(FLUX_CORE_INCLUDES) $^ -DCOMP_SERVICE=1 -fPIC -c -o $@

clean:
	rm *.o *.so
