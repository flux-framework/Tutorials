# Flux + Usernetes + Jupyter via KubeSpawner

This set of tutorials provides:

 - [Building Base Images](#build-images)
 - [Deploy A Cluster to AWS](#deploy-to-kubernetes)

Pre-requisites:

 - AWS account and aws client installed locally
 - Excitement to learn about Flux!

For AWS Tutorial Day users:

> To run the AWS tutorial, visit https://tutorial.flux-framework.org. You can use any login you want, but choose something relatvely uncommon  (like your email address) or you may end up sharing a JupyterLab instance with another user. The tutorial password will be provided to you. 

Since we start usernetes and build the container, the startup takes a few minutes, and we should start a little early (before the user expects to need it).

## Build Images

Unlike previous tutorials, since this one uses Usernetes and Flux, it is done via an EC2 instance, and we have built a custom EC2 spawner for it. This was built on a t4g.2xlarge instance, and then saved to an AMI. The logic is in [build](build).
  
## Deploy to AWS

### 1. Setup

#### IAM Policy

```bash
# Create the IAM policies
aws iam create-policy --policy-name JupyterHub-EC2-Manager-Policy --policy-document file://ec2/jupyterhub-ec2-policy.json
```
```console
{
    "Policy": {
        "PolicyName": "JupyterHub-EC2-Manager-Policy",
        "PolicyId": "ANPAZHDKVUIEA2NWPQFS4",
        "Arn": "arn:aws:iam::633731392008:policy/JupyterHub-EC2-Manager-Policy",
        "Path": "/",
        "DefaultVersionId": "v1",
        "AttachmentCount": 0,
        "PermissionsBoundaryUsageCount": 0,
        "IsAttachable": true,
        "CreateDate": "2025-07-31T22:54:06+00:00",
        "UpdateDate": "2025-07-31T22:54:06+00:00"
    }
}
```
And:

```bash
aws iam create-policy --policy-name JupyterHub-PassRole-Policy --policy-document file://jupyterhub-passrole-policy.json
```
```console
{
    "Policy": {
        "PolicyName": "JupyterHub-PassRole-Policy",
        "PolicyId": "ANPAZHDKVUIEMA2OTJQQS",
        "Arn": "arn:aws:iam::633731392008:policy/JupyterHub-PassRole-Policy",
        "Path": "/",
        "DefaultVersionId": "v1",
        "AttachmentCount": 0,
        "PermissionsBoundaryUsageCount": 0,
        "IsAttachable": true,
        "CreateDate": "2025-08-01T00:47:28+00:00",
        "UpdateDate": "2025-08-01T00:47:28+00:00"
    }
}
```
```bash
aws iam attach-role-policy \
    --role-name JupyterHub-EC2-Manager-Role \
    --policy-arn arn:aws:iam::633731392008:policy/JupyterHub-PassRole-Policy
```

```bash
# Create the IAM role that EC2 can assume
aws iam create-role --role-name JupyterHub-EC2-Manager-Role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }
}'
```
```console
{
    "Role": {
        "Path": "/",
        "RoleName": "JupyterHub-EC2-Manager-Role",
        "RoleId": "AROAZHDKVUIEJADZRZUZQ",
        "Arn": "arn:aws:iam::633731392008:role/JupyterHub-EC2-Manager-Role",
        "CreateDate": "2025-07-31T22:54:22+00:00",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        }
    }
}
```

```bash
# Attach the policy to the role
aws iam attach-role-policy --role-name JupyterHub-EC2-Manager-Role --policy-arn arn:aws:iam::633731392008:policy/JupyterHub-EC2-Manager-Policy

# Create an instance profile, which is the container for the role that EC2 uses
aws iam create-instance-profile --instance-profile-name JupyterHub-EC2-Manager-Profile
```
```console
{
    "InstanceProfile": {
        "Path": "/",
        "InstanceProfileName": "JupyterHub-EC2-Manager-Profile",
        "InstanceProfileId": "AIPAZHDKVUIEA6K5RNA33",
        "Arn": "arn:aws:iam::633731392008:instance-profile/JupyterHub-EC2-Manager-Profile",
        "CreateDate": "2025-07-31T22:55:40+00:00",
        "Roles": []
    }
}
```
```bash
aws iam add-role-to-instance-profile --instance-profile-name JupyterHub-EC2-Manager-Profile --role-name JupyterHub-EC2-Manager-Role
```

#### Security Group

Create the security group (we will do this once):

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region us-east-2)

# create the security group
SG_ID=$(aws ec2 create-security-group --group-name "JupyterHub-Hub-SG" --description "Security group for the main JupyterHub instance" --vpc-id $VPC_ID --query 'GroupId' --output text --region us-east-2)

# add rules to the security group for ssh from my address (so nobody is angry with me)
MY_IP=$(curl -s http://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr $MY_IP/32 --region us-east-2

# Allow HTTP (port 80) and HTTPS (port 443) from anywhere for users
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region us-east-2
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region us-east-2
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8888 --cidr 0.0.0.0/0 --region us-east-2
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region us-east-2
sudo python3 -m pip install pycurl --break-system-packages
# Created Security Group with ID: sg-05a9f952f6610732d
echo "Created Security Group with ID: $SG_ID"
```

#### Subnet

```bash
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query "Subnets[0].SubnetId" --output text --region us-east-2)
echo "Using Subnet ID: $SUBNET_ID"
# Using Subnet ID: subnet-0c8947f74b66f0579
```

#### Launch Instance

```bash
# This AMI has Flux, LAMMPS, Usernetes
AMI_ID="ami-0708f1489fd7a800b"
KEY_NAME="<KEYNAME>"
SECURITY_GROUP_ID="sg-05a9f952f6610732d"
SUBNET_ID="subnet-0c8947f74b66f0579"

aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --region us-east-2 \
    --instance-type "t4g.2xlarge" \
    --iam-instance-profile Name="JupyterHub-EC2-Manager-Profile" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SECURITY_GROUP_ID" \
    --subnet-id "$SUBNET_ID" \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=jupyter-hub-instance},{Key=Project,Value=HPCIC-2025-Tutorial}]' # \
# If we make a startup script.
#    --user-data file://hub-startup-script.sh
```

You can describe the instance to get the public ip.

```bash
aws ec2 describe-instances --region us-east-2
```

And ssh.

```bash
ssh -i ~/.ssh/<keyname>.pem -o IdentitiesOnly=yes ubuntu@3.136.154.184
sudo mkdir -p /srv/jupyterhub
# I copied jupyterhub_config.py and ec2_spawner.py there.
# Our custom login page needs to be in ./templates there too
```

I added access for my ip address:

```bash
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr $MY_IP/32 --region us-east-2
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8081 --cidr $MY_IP/32 --region us-east-2
```

#### Start Jupyter

```bash
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
sudo chown -R ubuntu /srv/jupyterhub/
export HUB_CONNECT_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4)
~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config.py

# Development (no culling)
~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config_no_culler.py

# To keep running
nohup ~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config.py &
```

Note that we will want to generate a certificate:

```bash
sudo apt-get install -y snapd
sudo snap install core; sudo snap refresh core

# Certbot!
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx
```
