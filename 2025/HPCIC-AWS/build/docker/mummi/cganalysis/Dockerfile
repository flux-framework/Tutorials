FROM 633731392008.dkr.ecr.us-east-1.amazonaws.com/mini-mummi:cganalysis-arm
RUN yum install -y tree
COPY ./entrypoint.sh /entrypoint.sh
# This is createsims output from /workdir/out
COPY ./data /tmp/out
ENTRYPOINT ["/bin/bash"]
CMD ["/entrypoint.sh"]
