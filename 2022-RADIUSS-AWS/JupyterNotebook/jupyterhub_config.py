c = get_config()  # noqa

# dummy for testing. Don't use this in production!
c.JupyterHub.authenticator_class = "dummy"

# self-signed cert. Don't use this in production!
c.JupyterHub.ssl_key = '/srv/jupyterhub/jupyter-selfsigned.key'
c.JupyterHub.ssl_cert = '/srv/jupyterhub/juptyer-selfsigned.crt'

# Or you can use certificates and keys from an 
# authority
# c.JupyterHub.ssl_key = '/srv/jupyterhub/privkey.pem'
# c.JupyterHub.ssl_cert = '/srv/jupyterhub/fullchain.pem'

# launch with docker
c.JupyterHub.spawner_class = "docker"

# we need the hub to listen on all ips when it is in a container
c.JupyterHub.hub_ip = '0.0.0.0'
# the hostname/ip that should be used to connect to the hub
# this is usually the hub container's name
c.JupyterHub.hub_connect_ip = 'jupyterhub'

# Uncomment to use HTTPS
# c.JupyterHub.port = 443

# pick a docker image. This should have the same version of jupyterhub
# in it as our Hub.
c.DockerSpawner.image = '<your image name>'

# tell the user containers to connect to our docker network
c.DockerSpawner.network_name = 'jupyterhub'

# delete containers when they stop
c.DockerSpawner.remove = True
# c.JupyterHub.shutdown_on_logout = True

# Extend the JupyterHub HTML templates
c.JupyterHub.template_paths = '/srv/jupyterhub/overrides/'

# Limit the spawned container resources
c.DockerSpawner.mem_limit = '4G'
c.DockerSpawner.cpu_limit = 1
