import asyncio
import boto3
from jupyterhub.spawner import Spawner
from traitlets import Unicode, Dict, List


class EC2Spawner(Spawner):
    """
    A Spawner for JupyterHub that launches a user's server on a new EC2 instance.
    """

    ami = Unicode(
        "ami-06cebbfb446ee0ceb",
        config=True,
        help="The AMI ID for the Flux + Usernetes VM.",
    )

    # The EC2 instance type
    instance_type = Unicode("t3g.2xlarge", config=True, help="The EC2 instance type.")

    # Always need the region
    region = Unicode("us-east-2", config=True, help="Region to deploy instance to")

    # The name of the EC2 key pair (leaving empty to not allow access)
    key_name = Unicode(
        "", config=True, help="The name of the EC2 key pair for ssh access."
    )

    # List of security group IDs
    security_group_ids = List(
        [], config=True, help="List of security group IDs for the instance."
    )

    # The IAM instance profile to attach to the instance
    iam_instance_profile_arn = Unicode(
        "",
        config=True,
        help="The ARN of the IAM instance profile to attach to the instance.",
    )

    # Tags to apply to the instance
    instance_tags = Dict(
        {"ManagedBy": "JupyterHub"},
        config=True,
        help="Tags to apply to the spawned EC2 instance.",
    )

    # The subnet to launch the instance in
    subnet_id = Unicode(
        "", config=True, help="The subnet ID to launch the instance in."
    )

    # We need to save the instance ID to be able to stop and poll it later.
    instance_id = Unicode()

    def _get_user_data(self):
        """
        Generates the UserData script to start the jupyter-lab server.
        This version correctly handles single quotes in environment variables.
        """
        user = "ubuntu"

        # Get environment variables from JupyterHub
        env_vars = self.get_env()

        # Properly escape single quotes within environment variable values
        # before wrapping them in single quotes for the export command.
        env_export_cmds = []
        for key, value in env_vars.items():
            # 1. Convert value to string
            value_str = str(value)
            # 2. Escape any single quotes by replacing ' with '\''
            escaped_value = value_str.replace("'", r"'\''")
            # 3. Create the export command
            env_export_cmds.append(f"export {key}='{escaped_value}'")

        # The user under which the jupyter-lab server will run
        # Script is written to: /var/lib/cloud/instance/scripts/part-001
        script = f"""#!/bin/bash
exec >> /var/log/user-data.log 2>&1
date
# This should be the script path
echo "$0"

# Load modules for usernetes
sudo modprobe ip6_tables
sudo modprobe ip6table_nat
sudo modprobe iptable_nat

make -C /home/ubuntu/usernetes up
sleep 3
echo "$!/bin/bash" >> /home/ubuntu/start-usernetes.sh
echo "make -C /home/ubuntu/usernetes kubeadm-init" >> /home/ubuntu/start-usernetes.sh
echo "make -C /home/ubuntu/usernetes install-flannel" >> /home/ubuntu/start-usernetes.sh
echo "make -C /home/ubuntu/usernetes kubeconfig" >> /home/ubuntu/start-usernetes.sh
echo "export KUBECONFIG=/home/ubuntu/usernetes/kubeconfig"
chmod +x /home/ubuntu/start-usernetes.sh

# This should already be done on the host
# sudo apt-get purge -y nodejs npm
# sudo apt-get autoremove -y
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt-get install -y nodejs
rm -rf /usr/local/bin/node

# Use sudo to switch to the user and bash to execute the script
sudo -i -u {user} bash << 'EOF'
#!/bin/bash
set -euo pipefail

echo "Running as user $(whoami) in $(pwd)"

# Export all the necessary environment variables for this shell
{chr(10).join(env_export_cmds)}

echo "Starting JupyterLab..."

flux start /usr/local/bin/jupyter-lab \\
  --ip=0.0.0.0 \\
  --port=8888 \\
  --IdentityProvider.token="" \\
  --ServerApp.password="" \\
  --ServerApp.base_url=$JUPYTERHUB_SERVICE_PREFIX \\
  --JupyterLabApp.hub_api_url=$JUPYTERHUB_API_URL \\
  --JupyterLabApp.hub_activity_url=$JUPYTERHUB_ACTIVITY_URL \\
  --JupyterLabApp.hub_prefix=$JUPYTERHUB_BASE_URL

echo "JupyterLab command finished."
EOF

echo "--- UserData Script Finished ---"
date
"""
        return script

    async def start(self):
        """
        Start the user's EC2 instance.
        """
        self.log.info(f"User {self.user.name}: Requesting to start EC2 instance.")

        ec2 = boto3.resource("ec2", region_name=self.region)

        # Create a unique tag for this user's instance
        tags = self.instance_tags.copy()
        tags["jupyterhub-user"] = self.user.name

        tag_spec = [
            {
                "ResourceType": "instance",
                "Tags": [{"Key": k, "Value": v} for k, v in tags.items()],
            }
        ]

        user_data_script = self._get_user_data()

        try:
            instance = ec2.create_instances(
                ImageId=self.ami,
                InstanceType=self.instance_type,
                KeyName=self.key_name,
                SecurityGroupIds=self.security_group_ids,
                SubnetId=self.subnet_id,
                IamInstanceProfile={"Arn": self.iam_instance_profile_arn},
                TagSpecifications=tag_spec,
                UserData=user_data_script,
                MinCount=1,
                MaxCount=1,
            )[0]
        except Exception as e:
            self.log.error(
                f"Failed to create EC2 instance for user {self.user.name}: {e}"
            )
            raise e

        self.instance_id = instance.id
        self.log.info(f"User {self.user.name}: Started instance {self.instance_id}")

        # Wait for the instance to be in 'running' state
        self.log.info(
            f"User {self.user.name}: Waiting for instance {self.instance_id} to be running..."
        )

        # Poll until the instance is running and has an IP
        while True:
            await asyncio.sleep(5)
            instance.reload()

            if instance.state["Name"] == "running":
                if instance.public_ip_address:
                    self.log.info(
                        f"User {self.user.name}: Instance {self.instance_id} is running at IP {instance.public_ip_address}"
                    )
                    # Return the IP and port for JupyterHub to proxy to
                    return (instance.public_ip_address, 8888)
                else:
                    self.log.info(
                        f"User {self.user.name}: Instance running but waiting for public IP..."
                    )
            elif instance.state["Name"] in [
                "shutting-down",
                "terminated",
                "stopping",
                "stopped",
            ]:
                error_msg = f"Instance {self.instance_id} entered state '{instance.state['Name']}' unexpectedly."
                self.log.error(error_msg)
                raise RuntimeError(error_msg)

    async def stop(self, now=False):
        """
        Stop and terminate the user's EC2 instance.
        """
        if not self.instance_id:
            self.log.info(f"User {self.user.name}: No instance ID found to stop.")
            return

        self.log.info(
            f"User {self.user.name}: Requesting to terminate instance {self.instance_id}"
        )
        ec2 = boto3.resource("ec2", region_name=self.region)
        instance = ec2.Instance(self.instance_id)

        try:
            instance.terminate()
            self.log.info(
                f"User {self.user.name}: Successfully terminated instance {self.instance_id}"
            )
        except Exception as e:
            # Handle cases where instance might already be terminated
            if "InvalidInstanceID.NotFound" in str(e):
                self.log.warning(f"Instance {self.instance_id} already terminated.")
            else:
                self.log.error(f"Failed to terminate instance {self.instance_id}: {e}")
                raise e

        self.clear_state()

    async def poll(self):
        """
        Check if the EC2 instance is still running.
        Returns:
          None if the instance is running.
          0 if the instance is stopped or terminated.
        """
        if not self.instance_id:
            return 0  # Not running

        ec2 = boto3.resource("ec2")
        instance = ec2.Instance(self.instance_id)

        try:
            instance.reload()
            state = instance.state["Name"]
            self.log.debug(f"Polling instance {self.instance_id}, state is: {state}")

            if state == "running":
                return None  # Still running
            else:
                return 0  # Not running (stopped, terminated, etc.)
        except Exception:
            # Instance not found, so it's not running
            self.log.warning(
                f"Polling failed for instance {self.instance_id}. Assuming it's terminated."
            )
            return 0

    # JupyterHub can remember the instance ID across restarts.
    def load_state(self, state):
        super().load_state(state)
        self.instance_id = state.get("instance_id", "")

    def get_state(self):
        state = super().get_state()
        if self.instance_id:
            state["instance_id"] = self.instance_id
        return state

    def clear_state(self):
        super().clear_state()
        self.instance_id = ""
