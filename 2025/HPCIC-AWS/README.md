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

Unlike previous tutorials, since this one uses Usernetes and Flux, it is done via an EC2 instance, and we have built a custom EC2 spawner for it. This was built on a t4g.2xlarge (Graviton 2) and then hpc7g.16xlarge (Graviton 3) instance, and then saved to an AMI. Incremental changes were saved from the image directly. Note that we needed to build the docker image for usernetes to be cached on the node before a save:

```bash
cd /home/ubuntu/usernetes
docker build -t usernetes_node .
```

The base logic is in [build](build).
  
## Deploy to AWS

**Do not forget to use the RADIUSS account**

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
aws iam create-policy --policy-name JupyterHub-PassRole-Policy --policy-document file://ec2/jupyterhub-passrole-policy.json
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
aws iam attach-role-policy \
    --role-name JupyterHub-EC2-Manager-Role \
    --policy-arn arn:aws:iam::633731392008:policy/JupyterHub-PassRole-Policy
```

```bash
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

#### Security Grouph

Create the security group (we will do this once):

```bash
# Get the default VPC (if subnets are in right region)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region us-east-1)

# Create a new VPC

# create the security group
SG_ID=$(aws ec2 create-security-group --group-name "JupyterHub-Hub-SG" --description "Security group for the main JupyterHub instance" --vpc-id $VPC_ID --query 'GroupId' --output text --region us-east-1)
# sg-0a3f6eea31df1b19c

# add rules to the security group for ssh from my address (so nobody is angry with me)
MY_IP=$(curl -s http://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr $MY_IP/32 --region us-east-1

# Allow HTTP (port 80) and HTTPS (port 443) from anywhere for users
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8888 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region us-east-1
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8001 --cidr 0.0.0.0/0 --region us-east-1

# Flux
# Created Security Group with ID: sg-05a9f952f6610732d
# RADIUSS
# Created Security Group with ID: sg-0a3f6eea31df1b19c
echo "Created Security Group with ID: $SG_ID"
# vpc-0722eea756bb11a06
```



#### Subnet

```bash
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query "Subnets[0].SubnetId" --output text --region us-east-1)
echo "Using Subnet ID: $SUBNET_ID"
# Using Subnet ID: subnet-0c8947f74b66f0579
```

#### Launch Instance

```bash
# This AMI has Flux, LAMMPS, Usernetes
AMI_ID="ami-0708f1489fd7a800b"
KEY_NAME="<KEYNAME>"
SECURITY_GROUP_ID="sg-05a9f952f6610732d"
# This is associated with vpc-0722eea756bb11a06 in RADIUSS "project" vpc
SUBNET_ID="subnet-0b80853238a402001"

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

## Suggestions

- Have usernetes start at startup
- Why is it starting in the ch4 directory
- mnist / lammps need explanation
- other chapters should have the same terminal setup
- put slides to have component and setup explanation
- add more intro section to explain kubectl get nodes, flux instance list, get output
- chapter 2 issue 

#### Start Jupyter

```bash
sudo chown -R ubuntu /srv/jupyterhub/
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
export HUB_CONNECT_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4)

# Kolomogorov

# Development (no culling)
~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config_no_culler.py

# With culling
~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config.py

# To keep running
screen
nohup ~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config.py &
```

#### SSL / Certificates

Note that we will want to generate a certificate. First, install and configure certbot.

```bash
# Certbot!
# tutorial.flux-framework.org
sudo systemctl stop nginx
sudo certbot certonly --standalone
sudo chown -R ubuntu /etc/letsencrypt/
```

Then add this content to `/etc/nginx/sites-available/default`

And restart:

```bash
sudo systemctl reload nginx
```

#### SSL and Snapshots

I originally created the AMI in the wrong account. To share between accounts I needed to take off automatic encryption of snapshots. This is `/etc/nginx/sites-enabled/default`

```
server {
    listen 80;
    server_name tutorial.flux-framework.org;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name tutorial.flux-framework.org;

    ssl_certificate /etc/letsencrypt/live/tutorial.flux-framework.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tutorial.flux-framework.org/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
	#proxy_set_header Upgrade $websocket_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

And then save a new one, getting the volume from the name.

```bash
# Create the snapshot
aws ec2 create-snapshot --volume-id vol-0db075348c995f4c1 --description "HPCIC Flux Tutorial 2025 JupyterHub EC2 Spawner (save August 5, 2025)" --region us-east-2

# and the image
aws ec2 register-image --name "hpcic-flux-tutorial-2025" --description "HPCIC Flux Framework Tutorial (JupyterHub Spawner EC2) 2025" --root-device-name /dev/sda1 --block-device-mappings "DeviceName=/dev/sda1,Ebs={SnapshotId=snap-0786282c76b84f55e}" --region us-east-2
```
