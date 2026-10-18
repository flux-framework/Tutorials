#!/usr/bin/env bash
# Check that the AWS resources for the Flux QRMI tutorial JupyterHub exist.
# This is the SC26-qrmi hub, separate from the SC26 hub. It has its own Name
# and Project tags so the two can run side by side in the same region and
# share the security group, role, and instance profile.
# Prints the command to create anything missing. If nothing is missing,
# prints the run-instances command for the hub.
#
# Run from the directory that contains ec2/*.json.
# Any variable below can be overridden from the environment.

set -uo pipefail

REGION="${REGION:-us-east-1}"
EXPECTED_ACCOUNT_ID="${EXPECTED_ACCOUNT_ID:-633731392008}"
INSTANCE_TYPE="${INSTANCE_TYPE:-hpc7g.16xlarge}"
AMI_ID="${AMI_ID:-ami-0e16d3f6d409182d3}"
KEY_NAME="${KEY_NAME:-ed-the-dinosaur}"
SG_ID="${SG_ID:-sg-0ddfbe3cd0f9253d3}"
SG_NAME="${SG_NAME:-JupyterHub-Hub-SG}"
POLICY_DIR="${POLICY_DIR:-ec2}"
HUB_TAG_NAME="${HUB_TAG_NAME:-jupyter-hub-qrmi-instance}"
PROJECT_TAG="${PROJECT_TAG:-SC26-QRMI-Tutorial}"
TUTORIALS_REPO="${TUTORIALS_REPO:-https://github.com/flux-framework/Tutorials}"
TUTORIALS_BRANCH="${TUTORIALS_BRANCH:-sc26-qrmi}"
TUTORIALS_DIR="${TUTORIALS_DIR:-2026/SC26-qrmi}"
HUB_CONFIG="${HUB_CONFIG:-ec2/jupyterhub_config.py}"

ROLE_NAME="JupyterHub-EC2-Manager-Role"
PROFILE_NAME="JupyterHub-EC2-Manager-Profile"
EC2_POLICY_NAME="JupyterHub-EC2-Manager-Policy"
PASSROLE_POLICY_NAME="JupyterHub-PassRole-Policy"
BRAKET_POLICY_NAME="JupyterHub-Braket-SV1-Policy"
PUBLIC_PORTS=(80 443 8888 8000 8001)

missing=0
fixes=()
ERR_FILE=$(mktemp)
trap 'rm -f "$ERR_FILE"' EXIT

ok()      { printf '  [ok]      %s\n' "$1"; }
warn()    { printf '  [warn]    %s\n' "$1"; }
bad()     { printf '  [missing] %s\n' "$1"; missing=$((missing + 1)); }
fix()     { fixes+=("$1"); }
section() { printf '\n== %s\n' "$1"; }

# Run aws, sending stderr to ERR_FILE.
awsq() { aws "$@" 2>"$ERR_FILE"; }

# Last non-empty line of the previous aws error.
last_err() { grep -v '^[[:space:]]*$' "$ERR_FILE" | tail -n 1 | sed 's/^aws: \[ERROR\]: //'; }

# Return 0 if the managed policy ARN is attached to the role.
role_has_policy() {
  local found
  found=$(awsq iam list-attached-role-policies --role-name "$1" \
    --query "AttachedPolicies[?PolicyArn=='$2'].PolicyArn" --output text) || return 1
  [[ -n "$found" && "$found" != "None" ]]
}

# Warn if a local policy document is missing.
check_policy_file() {
  [[ -f "$1" ]] || warn "local file $1 not found (needed only to create the policy)"
}

# Return 0 if the security group allows tcp/$1 from $2.
sg_allows() {
  local cidrs
  cidrs=$(awsq ec2 describe-security-groups --region "$REGION" --group-ids "$SG_ID" \
    --query "SecurityGroups[0].IpPermissions[?IpProtocol=='-1' || (IpProtocol=='tcp' && FromPort<=\`$1\` && ToPort>=\`$1\`)].IpRanges[].CidrIp" \
    --output text) || return 1
  grep -qwF -- "$2" <<<"$cidrs" || grep -qwF -- "0.0.0.0/0" <<<"$cidrs"
}

# ---------------------------------------------------------------------------
section "AWS identity"
command -v aws >/dev/null || { echo "aws CLI not found" >&2; exit 2; }
if ! ACCOUNT_ID=$(awsq sts get-caller-identity --query Account --output text); then
  echo "Cannot get caller identity: $(last_err)" >&2
  exit 2
fi
if [[ "$ACCOUNT_ID" == "$EXPECTED_ACCOUNT_ID" ]]; then
  ok "account $ACCOUNT_ID"
else
  warn "account is $ACCOUNT_ID, expected $EXPECTED_ACCOUNT_ID (RADIUSS?)"
fi

EC2_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${EC2_POLICY_NAME}"
PASSROLE_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${PASSROLE_POLICY_NAME}"
BRAKET_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${BRAKET_POLICY_NAME}"

# ---------------------------------------------------------------------------
section "IAM policies"
for pair in "$EC2_POLICY_NAME:jupyterhub-ec2-policy.json" \
            "$PASSROLE_POLICY_NAME:jupyterhub-passrole-policy.json" \
            "$BRAKET_POLICY_NAME:jupyterhub-braket-policy.json"; do
  name="${pair%%:*}"
  file="${POLICY_DIR}/${pair#*:}"
  if awsq iam get-policy --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${name}" >/dev/null; then
    ok "policy $name"
  else
    bad "policy $name ($(last_err))"
    check_policy_file "$file"
    fix "aws iam create-policy --policy-name $name --policy-document file://$file"
  fi
done

# ---------------------------------------------------------------------------
section "IAM role and instance profile"
if awsq iam get-role --role-name "$ROLE_NAME" >/dev/null; then
  ok "role $ROLE_NAME"
  role_exists=1
else
  bad "role $ROLE_NAME ($(last_err))"
  role_exists=0
  fix "aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document '{
  \"Version\": \"2012-10-17\",
  \"Statement\": {
    \"Effect\": \"Allow\",
    \"Principal\": {\"Service\": \"ec2.amazonaws.com\"},
    \"Action\": \"sts:AssumeRole\"
  }
}'"
fi

for arn in "$PASSROLE_POLICY_ARN" "$BRAKET_POLICY_ARN"; do
  if (( role_exists )) && role_has_policy "$ROLE_NAME" "$arn"; then
    ok "role has ${arn##*/}"
  else
    bad "role does not have ${arn##*/} attached"
    fix "aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $arn"
  fi
done

# The README creates this policy but never attaches it, so only warn.
if (( role_exists )) && role_has_policy "$ROLE_NAME" "$EC2_POLICY_ARN"; then
  ok "role has $EC2_POLICY_NAME"
else
  warn "role does not have $EC2_POLICY_NAME attached (README never attaches it). If needed:"
  warn "  aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn $EC2_POLICY_ARN"
fi

if roles=$(awsq iam get-instance-profile --instance-profile-name "$PROFILE_NAME" \
    --query 'InstanceProfile.Roles[].RoleName' --output text); then
  ok "instance profile $PROFILE_NAME"
  if grep -qwF -- "$ROLE_NAME" <<<"$roles"; then
    ok "instance profile contains $ROLE_NAME"
  else
    bad "instance profile does not contain $ROLE_NAME"
    fix "aws iam add-role-to-instance-profile --instance-profile-name $PROFILE_NAME --role-name $ROLE_NAME"
  fi
else
  bad "instance profile $PROFILE_NAME ($(last_err))"
  fix "aws iam create-instance-profile --instance-profile-name $PROFILE_NAME"
  fix "aws iam add-role-to-instance-profile --instance-profile-name $PROFILE_NAME --role-name $ROLE_NAME"
fi

slr=$(awsq iam list-roles --path-prefix /aws-service-role/braket.amazonaws.com/ \
  --query 'Roles[].RoleName' --output text)
if [[ -n "$slr" && "$slr" != "None" ]]; then
  ok "Braket service-linked role ($slr)"
else
  bad "Braket service-linked role"
  fix "aws iam create-service-linked-role --aws-service-name braket.amazonaws.com"
fi

# ---------------------------------------------------------------------------
section "EC2 ($REGION)"
if state=$(awsq ec2 describe-images --region "$REGION" --image-ids "$AMI_ID" \
    --query 'Images[0].State' --output text) && [[ "$state" == "available" ]]; then
  ok "AMI $AMI_ID"
else
  bad "AMI $AMI_ID (state: ${state:-$(last_err)}). No command; rebuild per 'Build Images'."
fi

if awsq ec2 describe-key-pairs --region "$REGION" --key-names "$KEY_NAME" >/dev/null; then
  ok "key pair $KEY_NAME"
else
  bad "key pair $KEY_NAME ($(last_err))"
  fix "aws ec2 create-key-pair --region $REGION --key-name $KEY_NAME --query KeyMaterial --output text > ~/.ssh/$KEY_NAME.pem && chmod 400 ~/.ssh/$KEY_NAME.pem"
fi
[[ -f "$HOME/.ssh/$KEY_NAME.pem" ]] || warn "$HOME/.ssh/$KEY_NAME.pem not found locally"

VPC_ID=""
if VPC_ID=$(awsq ec2 describe-security-groups --region "$REGION" --group-ids "$SG_ID" \
    --query 'SecurityGroups[0].VpcId' --output text); then
  ok "security group $SG_ID (vpc $VPC_ID)"
else
  err=$(last_err)
  found=$(awsq ec2 describe-security-groups --region "$REGION" \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].[GroupId,VpcId]' --output text)
  if [[ -n "$found" && "$found" != "None" ]]; then
    read -r SG_ID VPC_ID <<<"$found"
    warn "security group by id not found; using $SG_NAME = $SG_ID (vpc $VPC_ID)"
  else
    VPC_ID=""
    bad "security group $SG_ID / $SG_NAME ($err)"
    fix "VPC_ID=\$(aws ec2 describe-vpcs --filters \"Name=isDefault,Values=true\" --query \"Vpcs[0].VpcId\" --output text --region $REGION)
SG_ID=\$(aws ec2 create-security-group --group-name \"$SG_NAME\" --description \"Security group for the main JupyterHub instance\" --vpc-id \$VPC_ID --query 'GroupId' --output text --region $REGION)
echo \$SG_ID   # then re-run this script with SG_ID=<that id>"
  fi
fi

if [[ -n "$VPC_ID" ]]; then
  MY_IP=$(curl -s --max-time 5 http://checkip.amazonaws.com || true)
  if [[ -z "$MY_IP" ]]; then
    warn "could not determine public IP; skipping ssh rule check"
  elif sg_allows 22 "$MY_IP/32"; then
    ok "port 22 open to $MY_IP/32"
  else
    bad "port 22 not open to $MY_IP/32"
    fix "aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr $MY_IP/32 --region $REGION"
  fi
  for port in "${PUBLIC_PORTS[@]}"; do
    if sg_allows "$port" "0.0.0.0/0"; then
      ok "port $port open to 0.0.0.0/0"
    else
      bad "port $port not open to 0.0.0.0/0"
      fix "aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port $port --cidr 0.0.0.0/0 --region $REGION"
    fi
  done
fi

TARGET_AZ=$(awsq ec2 describe-instance-type-offerings --region "$REGION" \
  --location-type availability-zone \
  --filters "Name=instance-type,Values=$INSTANCE_TYPE" \
  --query 'InstanceTypeOfferings[0].Location' --output text)
if [[ -z "$TARGET_AZ" || "$TARGET_AZ" == "None" ]]; then
  bad "no AZ in $REGION offers $INSTANCE_TYPE $(last_err)"
  TARGET_AZ=""
else
  ok "$INSTANCE_TYPE offered in $TARGET_AZ"
fi

SUBNET_ID=""
if [[ -n "$VPC_ID" && -n "$TARGET_AZ" ]]; then
  SUBNET_ID=$(awsq ec2 describe-subnets --region "$REGION" \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=$TARGET_AZ" \
    --query 'Subnets[0].SubnetId' --output text)
  if [[ -n "$SUBNET_ID" && "$SUBNET_ID" != "None" ]]; then
    ok "subnet $SUBNET_ID ($VPC_ID, $TARGET_AZ)"
  else
    SUBNET_ID=""
    bad "no subnet in $VPC_ID / $TARGET_AZ $(last_err)"
    fix "# only works if $VPC_ID is the default VPC
aws ec2 create-default-subnet --availability-zone $TARGET_AZ --region $REGION"
  fi
fi

# ---------------------------------------------------------------------------
section "Tutorial sources and hub config"
# The spawner clones this branch at launch, so it has to exist before anyone logs in
if git ls-remote --exit-code --heads "$TUTORIALS_REPO" "$TUTORIALS_BRANCH" >/dev/null 2>&1; then
  ok "branch $TUTORIALS_BRANCH in $TUTORIALS_REPO"
  if curl -fsI "https://raw.githubusercontent.com/${TUTORIALS_REPO#https://github.com/}/$TUTORIALS_BRANCH/$TUTORIALS_DIR/ec2/start-usernetes.sh" >/dev/null 2>&1; then
    ok "$TUTORIALS_DIR present on $TUTORIALS_BRANCH"
  else
    bad "$TUTORIALS_DIR/ec2/start-usernetes.sh not found on $TUTORIALS_BRANCH. Push the qrmi directory there."
  fi
else
  bad "branch $TUTORIALS_BRANCH not found in $TUTORIALS_REPO. Push it; the spawner clones it at launch."
fi
if [[ -f "$HUB_CONFIG" ]]; then
  cfg_ami=$(grep -oE '^c\.EC2Spawner\.ami *= *"[^"]+"' "$HUB_CONFIG" | grep -oE 'ami-[0-9a-f]+')
  if [[ "$cfg_ami" == "$AMI_ID" ]]; then
    ok "$HUB_CONFIG spawns $AMI_ID"
  else
    bad "$HUB_CONFIG spawns ${cfg_ami:-nothing}, expected $AMI_ID"
    fix "sed -i 's|^c.EC2Spawner.ami = .*|c.EC2Spawner.ami = \"$AMI_ID\"|' $HUB_CONFIG"
  fi
  grep -q 'DummyAuthenticator.password = "REPLACEME"' "$HUB_CONFIG" \
    && warn "$HUB_CONFIG still has the REPLACEME password; set it on the hub, not in git"
else
  warn "$HUB_CONFIG not found, cannot check the spawned AMI"
fi

existing=$(awsq ec2 describe-instances --region "$REGION" \
  --filters "Name=tag:Name,Values=$HUB_TAG_NAME" \
            "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]' --output text)
if [[ -n "$existing" ]]; then
  while read -r line; do warn "existing hub instance: $line"; done <<<"$existing"
fi

# ---------------------------------------------------------------------------
echo
if (( missing > 0 )); then
  echo "== $missing missing item(s). Commands to fix, in order:"
  echo
  for cmd in "${fixes[@]}"; do
    printf '%s\n\n' "$cmd"
  done
  echo "Then re-run this script."
  exit 1
fi

echo "== Everything exists. Launch the hub with:"
echo
cat <<EOF
aws ec2 run-instances \\
    --image-id "$AMI_ID" \\
    --region $REGION \\
    --instance-type "$INSTANCE_TYPE" \\
    --iam-instance-profile Name="$PROFILE_NAME" \\
    --key-name "$KEY_NAME" \\
    --security-group-ids "$SG_ID" \\
    --subnet-id "$SUBNET_ID" \\
    --associate-public-ip-address \\
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=$HUB_TAG_NAME},{Key=Project,Value=$PROJECT_TAG}]'
EOF
