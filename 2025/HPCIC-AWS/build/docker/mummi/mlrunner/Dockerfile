FROM 633731392008.dkr.ecr.us-east-1.amazonaws.com/mini-mummi:mlrunner-arm
RUN yum install -y tree
COPY ./entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/bash"]
CMD ["/entrypoint.sh"]
