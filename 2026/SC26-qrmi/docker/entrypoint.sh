#!/bin/bash
# JupyterHub single-user entrypoint. The hub spawns this instead of the CMD,
# so start the instance the same way and make the single-user server its
# initial program. The image ENTRYPOINT (docker-entrypoint) has already
# dropped to the tutorial user by the time this runs.
exec flux-quantum-start -- jupyterhub-singleuser "$@"
