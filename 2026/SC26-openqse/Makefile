# QFw on Flux tutorial
#
#   make build            build the image (long the first time)
#   make run              start it, then open http://localhost:8888
#   make shell            a root shell in the running container
#   make push             push the image to ghcr.io (docker login ghcr.io first)
IMAGE ?= ghcr.io/flux-framework/tutorials:sc26-openqse
NAME ?= sc26-openqse
FLUX_QFW_REF ?= updates
PORT ?= 8888
QFW_BUILD_JOBS ?= 4

.PHONY: build run shell push

build:
	docker build --build-arg QFW_BUILD_JOBS=$(QFW_BUILD_JOBS) \
		--build-arg FLUX_QFW_REF=$(FLUX_QFW_REF) -t $(IMAGE) .

run:
	docker run --rm --name $(NAME) -p 127.0.0.1:$(PORT):8888 $(IMAGE)

shell:
	docker exec -it $(NAME) bash

push:
	docker push $(IMAGE)
