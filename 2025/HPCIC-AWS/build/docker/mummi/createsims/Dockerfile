FROM ghcr.io/converged-computing/mummi-experiments:cpu-node-selector-arm
RUN yum install -y tree
COPY ./entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/bash"]
CMD ["/entrypoint.sh"]
