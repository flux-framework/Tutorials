#!/bin/sh

# Copy the notebook icon
# This would be for the customized launcher, not working yet
# wget https://flux-framework.org/assets/images/Flux-logo-mark-only-full-color.png
# mv Flux-logo-mark-only-full-color.png /home/jovyan/flux-icon.png

# We need to clone to the user home, and then change permissions to uid 1000
# That uid is shared by jovyan here and the spawn container
chown -R 1000 /home/jovyan
