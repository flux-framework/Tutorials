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

Unlike previous tutorials, since this one uses Usernetes and Flux, it is done via an EC2 instance, and we have built a custom EC2 spawner for it. This was built on a hpc7g.16xlarge (Graviton 3) instance, and then saved to an AMI. Incremental changes were saved from the image directly. Note that we needed to build the docker image for usernetes to be cached on the node before a save:

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

#### Braket Policy (for the Chapter 5 quantum demo)

The Chapter 5 notebook runs a hybrid quantum-classical QAOA workload against the AWS Braket SV1 simulator. The spawned user instances use the `JupyterHub-EC2-Manager-Role` (see `iam_instance_profile_arn` in `ec2/jupyterhub_config.py`), so we attach a Braket policy to that same role. The Braket SDK then picks up the instance-role credentials from instance metadata — no keys are stored on the VM.

The policy in `ec2/jupyterhub-braket-policy.json` is least-privilege and, per our AWS admin's recommendation, scopes the device-level actions (`braket:GetDevice`, `braket:CreateQuantumTask`) to just the SV1 device ARN `arn:aws:braket:::device/quantum-simulator/amazon/sv1`. It also allows the task polling/search actions (which do not accept a device ARN as a resource) and S3 access to the `amazon-braket-*` results bucket that SV1 writes to.

First, capture your AWS account ID into an environment variable so the rest of the commands are copy-paste ready:

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Using account: ${ACCOUNT_ID}"
```

Create the Braket policy and capture its ARN directly from the API response:

```bash
export BRAKET_POLICY_ARN=$(aws iam create-policy \
    --policy-name JupyterHub-Braket-SV1-Policy \
    --policy-document file://ec2/jupyterhub-braket-policy.json \
    --query 'Policy.Arn' --output text)
echo "Created policy: ${BRAKET_POLICY_ARN}"
```

If the policy already exists (so `create-policy` errored), derive its ARN from the account ID instead:

```bash
export BRAKET_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/JupyterHub-Braket-SV1-Policy"
```

Attach it to the role used by the spawned user instances:

```bash
aws iam attach-role-policy \
    --role-name JupyterHub-EC2-Manager-Role \
    --policy-arn "${BRAKET_POLICY_ARN}"
```

Finally, enable Braket in the account once by creating its service-linked role (this is an account-level admin step, intentionally NOT granted to the instance role). It is safe to re-run — if the role already exists you get a harmless error.

```bash
aws iam create-service-linked-role --aws-service-name braket.amazonaws.com
```

> Note: if `braket:CreateQuantumTask` is ever denied despite the device-scoped statement, widen the resource on that one action to also include the account's quantum-task ARN. Using the `ACCOUNT_ID` env var from above, that is `arn:aws:braket:us-east-1:${ACCOUNT_ID}:quantum-task/*`. The device-ARN scoping matches AWS's documented device-restriction model and is what the admin recommended, so start there.

#### Security Grouph

Create the security group (we will do this once):

```bash
# Get the default VPC (if subnets are in right region)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region us-east-1)

# Create a new VPC

# create the security group
SG_ID=$(aws ec2 create-security-group --group-name "JupyterHub-Hub-SG" --description "Security group for the main JupyterHub instance" --vpc-id $VPC_ID --query 'GroupId' --output text --region us-east-1)

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
# Created Security Group with ID: sg-0ddfbe3cd0f9253d3
```

#### Subnet

```bash
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=map-public-ip-on-launch,Values=true" --query "Subnets[0].SubnetId" --output text --region us-east-1)
echo "Using Subnet ID: $SUBNET_ID"
# Using Subnet ID: subnet-0e3f3782bee64eede
```

#### Launch Instance

```bash
# 1) Which AZs actually offer hpc7g.16xlarge in us-east-1?
aws ec2 describe-instance-type-offerings \
  --region us-east-1 \
  --location-type availability-zone \
  --filters Name=instance-type,Values=hpc7g.16xlarge \
  --query 'InstanceTypeOfferings[].Location' --output text

# 2) Grab the first offered AZ into an env var
export TARGET_AZ=$(aws ec2 describe-instance-type-offerings \
  --region us-east-1 \
  --location-type availability-zone \
  --filters Name=instance-type,Values=hpc7g.16xlarge \
  --query 'InstanceTypeOfferings[0].Location' --output text)
echo "Target AZ: $TARGET_AZ"

# 3) Find the VPC your current (wrong-AZ) subnet belongs to
export VPC_ID=$(aws ec2 describe-subnets --region us-east-1 \
  --subnet-ids "$SUBNET_ID" --query 'Subnets[0].VpcId' --output text)
echo "VPC: $VPC_ID"

# 4) Reassign SUBNET_ID to a subnet in that VPC that lives in the target AZ
export SUBNET_ID=$(aws ec2 describe-subnets --region us-east-1 \
  --filters Name=vpc-id,Values=$VPC_ID Name=availability-zone,Values=$TARGET_AZ \
  --query 'Subnets[0].SubnetId' --output text)
echo "New subnet: $SUBNET_ID"
```
```console
us-east-1a
Target AZ: us-east-1a
VPC: vpc-0231726e66ed7bb8b
New subnet: subnet-0b0e2408f9960d3f6
```

```bash
# This AMI has Flux, LAMMPS, Usernetes
AMI_ID="ami-0f8da7e8cf5544ed0"
KEY_NAME="ed-the-dinosaur"
SECURITY_GROUP_ID="sg-0ddfbe3cd0f9253d3"

aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --region us-east-1 \
    --instance-type "hpc7g.16xlarge" \
    --iam-instance-profile Name="JupyterHub-EC2-Manager-Profile" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SECURITY_GROUP_ID" \
    --subnet-id "$SUBNET_ID" \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=jupyter-hub-instance},{Key=Project,Value=HPCIC-2025-Tutorial}]' 

# If we make a startup script.
#    --user-data file://hub-startup-script.sh
```

You can describe the instance to get the public ip.

```bash
aws ec2 describe-instances --region us-east-1
```

And ssh.

```bash
ssh -i ~/.ssh/<keyname>.pem -o IdentitiesOnly=yes ubuntu@13.220.230.82
sudo mkdir -p /srv/jupyterhub
# I copied jupyterhub_config.py and ec2_spawner.py there.
# Our custom login page needs to be in ./templates there too
```

For the login page, you can also replace the default:

```bash
cp /home/ubuntu/.local/share/jupyterhub/templates/login.html ./old-login.html
cp login.html /home/ubuntu/.local/share/jupyterhub/templates/login.html
```

I added access for my ip address:

```bash
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr $MY_IP/32 --region us-east-2
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8081 --cidr $MY_IP/32 --region us-east-2
```

#### Start Jupyter

```bash
sudo chown -R ubuntu /srv/jupyterhub/
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
export HUB_CONNECT_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4)

# Development (no culling)
# ~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config_no_culler.py

# With culling
~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config.py

# To keep running
screen
nohup ~/.local/bin/jupyterhub -f /srv/jupyterhub/jupyterhub_config.py &
```

#### SSL / Certificates

Note that we will want to generate a certificate. First, install and configure certbot.

```bashlets
# Certbot!
# tutorial.flux-framework.org
sudo systemctl stop nginx
sudo certbot certonly --standalone
sudo chown -R ubuntu /etc/letsencrypt/
```

Then add this content to `/etc/nginx/sites-available/default`

```console
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
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

And restart:

```bash
sudo systemctl start nginx

# If already started...
sudo systemctl reload nginx
```

