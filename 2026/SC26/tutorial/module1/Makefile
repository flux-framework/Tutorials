MPICC := /opt/amazon/openmpi/bin/mpicc
ifeq ($(wildcard $(MPICC)),)
MPICC := mpicc
endif

make:
	$(MPICC) -o hello hello.c
