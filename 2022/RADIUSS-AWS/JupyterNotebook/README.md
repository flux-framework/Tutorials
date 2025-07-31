To run the AWS tutorial, visit https://tutorial.flux-framework.org 
You can use any login you want, but choose something relatvely uncommon 
(like your email address) or you may end up sharing a JupyterLab 
instance with another user. The tutorial password will be provided to you. 

If you have Docker available, you can build and run the tutorial with:

```
docker build --build-arg GLOBAL_PASSWORD=<password of your choice> -t <desired image name> -f Dockerfile.hub .
docker build -t <desired image name> -f Dockerfile.spawn .
# You will need to change the spawner image name (`c.DockerSpawner.image`) in 
# jupyterhub_config.py to the name you chose.
# Create the jupyter network in Docker:
docker network create jupyterhub
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock --net jupyterhub --name jupyterhub -p 8000:8000 <hub image name>
```
Then you can point your browser to https://localhost:8000. You will need 
to override your browser's warning about the certificate in this configuration, too.

