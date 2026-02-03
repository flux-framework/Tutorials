# Flux Jupyter Tutorial

This set of tutorials provides:

 - [Building Tutorial Image](#build-images)

Pre-requisites:

 - Docker client installed locally
 - Excitement to learn about Flux!

## Build Image

Build the tutorial image.

```bash
docker build -f ./docker/Dockerfile -t hpsf-flux .
```

## Run Image

Run the Image.

```bash
docker run --rm -it  -v /var/run/docker.sock:/var/run/docker.sock --name jupyterhub  -p 8888:8888 hpsf-flux
```
