# jupyterhub_config.py
#
# Configuration for JupyterHub running on a dedicated EC2 instance,
# spawning single-user servers on separate EC2 instances.
#
# This file should be placed in the same directory as ec2_spawner.py
# and where you run the 'jupyterhub' command.
#
# Assumed Directory Structure:
# /srv/jupyterhub/
#  ├── jupyterhub_config.py (this file)
#  └── ec2_spawner.py       (the custom spawner class file)

import os
import sys

# c is a global traitlets config object that JupyterHub provides.
c = get_config()

# -----------------------------------------------------------------------------
# Core JupyterHub Settings
# -----------------------------------------------------------------------------

# Tell JupyterHub to use your custom spawner class.
# We add '.' to the path to make sure Python can find ec2_spawner.py
# in the current directory.
sys.path.insert(0, os.path.dirname(__file__))
c.JupyterHub.spawner_class = "ec2_spawner.EC2Spawner"

# Custom login page
c.JupyterHub.template_paths = ["/srv/jupyterhub/templates"]
c.JupyterHub.static_paths = ["/srv/jupyterhub/static"]

# IP and Port for the Hub to listen on.
# '0.0.0.0' makes it listen on all network interfaces.
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_port = 8081

# The public-facing URL of the proxy.
# You should have a web server (like NGINX) or a Load Balancer in front
# of JupyterHub listening on port 80/443 and proxying to this port.
c.JupyterHub.proxy_api_ip = "127.0.0.1"
c.JupyterHub.proxy_api_port = 8001  # Default, can be left alone

# The public IP of this Hub machine. This is CRITICAL.
# The single-user servers on other EC2 instances need this IP to talk back to the Hub.
# It is highly recommended to set this via an environment variable.
# Before starting JupyterHub, you would run:
# export HUB_CONNECT_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
hub_connect_ip = os.environ.get("HUB_CONNECT_IP")
if not hub_connect_ip:
    raise RuntimeError(
        "HUB_CONNECT_IP environment variable must be set to the private IP of the Hub instance."
    )
c.JupyterHub.hub_connect_ip = hub_connect_ip


# -----------------------------------------------------------------------------
# Authenticator Settings
# -----------------------------------------------------------------------------
# For a tutorial, DummyAuthenticator is simple. Users can enter any username
# and the password specified below.
# For production, you would switch to OAuthenticator (e.g., with GitHub or Google).
c.JupyterHub.authenticator_class = "dummy"
c.DummyAuthenticator.password = "chicken-nuggers"

# Grant admin rights to a specific user for monitoring and management.
c.Authenticator.admin_users = {"admin"}

# We need to make this longer for usernetes to start
c.Spawner.start_timeout = 300
c.Spawner.http_timeout = 300
c.EC2Spawner.http_timeout = 300
c.EC2Spawner.start_timeout = 300

# -----------------------------------------------------------------------------
# Custom EC2Spawner Settings
# -----------------------------------------------------------------------------
# These are the settings for your custom ec2_spawner.py class.

# The AMI ID for the tutorial user VM. This AMI should have Python, JupyterLab,
# Usernetes, and all tutorial dependencies pre-installed.
c.EC2Spawner.ami = "ami-04c84d7b6a360f1a3"

# Instance type for each user's server.
# 't4g.2xlarge' is what had a maximum fom per core ratio in my experiments
c.EC2Spawner.instance_type = "t4g.2xlarge"

# The name of the EC2 key pair for SSH access (for debugging).
# We should remove this for actual tutorial.
c.EC2Spawner.key_name = "dinosaur-rsa"

# Security Group for the spawned instances. Must allow port 8888 ingress
# from this Hub's security group, and port 22 for your SSH access.
c.EC2Spawner.security_group_ids = ["sg-05a9f952f6610732d"]

# The VPC subnet to launch the instances in. Must have internet access.
c.EC2Spawner.subnet_id = "subnet-0c8947f74b66f0579"

# The IAM role for the *spawned* user instances. This role can grant permissions
# to S3, etc., if the tutorial needs it. This is attached to the user VM.
c.EC2Spawner.iam_instance_profile_arn = (
    "arn:aws:iam::633731392008:instance-profile/JupyterHub-EC2-Manager-Profile"
)

# Custom tags to apply to each spawned EC2 instance for tracking.
c.EC2Spawner.instance_tags = {
    "ManagedBy": "JupyterHub",
    "Project": "HPCIC-2025-Tutorial",
    "Purpose": "User-Server",
}


# -----------------------------------------------------------------------------
# Service: Idle Culler
# -----------------------------------------------------------------------------
# This service is ESSENTIAL for cost management. It will automatically shut down
# (and terminate, via our spawner's stop() method) idle user servers.

c.JupyterHub.load_roles = [
    {
        "name": "jupyterhub-idle-culler-role",
        "scopes": [
            "list:users",
            "read:users:activity",
            "delete:servers",
            # The admin:servers scope is required for the culler to see and stop all servers.
            "admin:servers",
        ],
        "services": ["jupyterhub-idle-culler-service"],
    }
]

c.JupyterHub.services = [
    {
        "name": "jupyterhub-idle-culler-service",
        "admin": True,  # The service needs admin permissions to stop other user's servers
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_idle_culler",
            # Timeout in seconds. 3600 = 1 hour.
            # Set this to a value appropriate for your tutorial.
            "--timeout=3600",
            # Check every 5 minutes
            "--cull-every=300",
        ],
    }
]

# -----------------------------------------------------------------------------
# Persistence
# -----------------------------------------------------------------------------
# Store the JupyterHub database in a persistent location on the Hub VM.
# This ensures that if you restart JupyterHub, it remembers active users and their
# associated EC2 instance IDs.
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/jupyterhub.sqlite"

# -----------------------------------------------------------------------------
# Other Optional Settings
# -----------------------------------------------------------------------------

# Concurrent spawn limit to prevent runaway costs if many people
# log in at once. Should be slightly higher than your expected user count.
c.JupyterHub.concurrent_spawn_limit = 120

# Memory limit for the Hub process itself (not the user servers).
# The default is usually fine.
# c.JupyterHub.cookie_secret_file = '/srv/jupyterhub/jupyterhub_cookie_secret' # Optional, but good practice
