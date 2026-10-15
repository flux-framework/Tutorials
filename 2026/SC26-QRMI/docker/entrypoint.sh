#!/bin/bash
# JupyterHub single-user entrypoint. The hub spawns this instead of the CMD,
# so start the instance the same way and make the single-user server its
# initial program. jupyterhub-singleuser is in /opt/venv/bin, on PATH.
exec flux-quantum-start -- jupyterhub-singleuser "$@"
