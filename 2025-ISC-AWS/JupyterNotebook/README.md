# Flux + Jupyter via KubeSpawner

This set of tutorials provides:

 - [Building Base Images](#build-images)
 - [Local Development or Usage](#local-usage)
 - [Deploy A Cluster to AWS or Google Cloud Using](#deploy-to-kubernetes) using Google Cloud or AWS

Pre-requisites:

 - kubectl, (eksctl|gcloud), and (optionally) docker installed locally
 - A cloud with a Kubernetes cluster deployed (AWS and Google)
 - Excitement to learn about Flux!

For AWS Tutorial Day users:

> To run the AWS tutorial, visit https://tutorial.flux-framework.org. You can use any login you want, but choose something relatvely uncommon  (like your email address) or you may end up sharing a JupyterLab  instance with another user. The tutorial password will be provided to you. 

## Build Images

Let's build a set of images - one spawner and one hub, and an init. You can customize the tag to your liking.
Remember that if you just want to test locally, you can jump to the [local usage](#local-usage) section.

```bash
docker build -t ghcr.io/flux-framework/flux-jupyter-hub:hpcic-2024 -f docker/Dockerfile.hub .
docker build -t ghcr.io/flux-framework/flux-jupyter-spawn:hpcic-2024 -f docker/Dockerfile.spawn .
docker build -t ghcr.io/flux-framework/flux-jupyter-init:hpcic-2024 -f docker/Dockerfile.init .
```

Note that these are available under the flux-framework organization GitHub packages, so you shouldn't need
to build them unless you are developing or changing them. 

If you do build (and use a different name) be sure to push your images to a public registry (or load them locally to your development cluster).
  
## Local Usage

While the tutorial here is intended for deployment on AWS or Google Cloud, you can also give it a try on your local machine with a single container! You will need to [install Docker](https://docs.docker.com/engine/install/). When you have Docker available, you can build and run the tutorial with:

```bash
docker build -t flux-tutorial -f docker/Dockerfile.spawn .
docker network create jupyterhub

# Here is how to run an entirely contained tutorial (the notebook in the container)
docker run --rm -it --entrypoint /start.sh -v /var/run/docker.sock:/var/run/docker.sock --net jupyterhub --name jupyterhub -p 8888:8888 flux-tutorial
```

If you want to develop the ipynb files, you can bind the tutorials directory:

```bash
docker run --rm -it --entrypoint /start.sh -v $PWD/tutorial:/home/jovyan/flux-tutorial-2024 -v /var/run/docker.sock:/var/run/docker.sock --net jupyterhub --name jupyterhub -p 8888:8888 flux-tutorial
```

And then editing and saving will save to your host. You can also File -> Download if you forget to do
this bind. Either way, when the container is running you can open the localhost or 127.0.0.1 (home sweet home!) link in your browser on port 8888. You'll want to go to flux-tutorial-2024 -> notebook to see the notebook.
You'll need to select http only (and bypass the no certificate warning).

## Deploy to Kubernetes

### 1. Create Cluster

#### Google Cloud

Here is how to create the cluster on Google Cloud using [gcloud](https://cloud.google.com/sdk/docs/install) (and assuming you have logged in
with [gcloud auth login](https://cloud.google.com/sdk/gcloud/reference/auth/login):

```bash
export GOOGLE_PROJECT=myproject
gcloud container clusters create flux-jupyter --project $GOOGLE_PROJECT \
    --zone us-central1-a --machine-type n1-standard-2 \
    --num-nodes=4 --enable-network-policy --enable-intra-node-visibility
```

#### AWS

Here is how to create an equivalent cluster on AWS (EKS). We will be using [eksctl](https://eksctl.io/introduction/), which
you should install.

```bash
# Create an EKS cluster with autoscaling with default storage
eksctl create cluster --config-file aws/eksctl-config.yaml

# Create an EKS cluster with io1 node storage but no autoscaling, used for the HPCIC 2024 tutorial
eksctl create cluster --config-file aws/eksctl-hpcic-tutorial-2023.yaml
```

You can find vanilla (manual) instructions [here](https://z2jh.jupyter.org/en/stable/kubernetes/amazon/step-zero-aws-eks.html) if you
are interested in how it works. We emulate the logic there using eksctl. Then generate a secret token - we will add this to [config-aws.yaml](aws/config-aws.yaml) (without SSL) or [config-aws-ssl.yaml](aws/config-aws-ssl.yaml) (with SSL). When your cluster is ready, this will deploy an EBS CSI driver:

```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
```

And install the cluster-autoscaler:

```bash
kubectl apply -f aws/cluster-autoscaler-autodiscover.yaml 
```

If you want to use a different storage class than the default (`gp2`), you also need to create the new storage class (`gp3` here) and set it as the default storage class:

```bash
kubectl apply -f aws/storageclass.yaml
kubectl patch storageclass gp3 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
kubectl patch storageclass gp2 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

Most of the information I needed to read about this was [here](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md) - the Jupyter documentation wasn't super helpful beyond saying to install it. Also note that I got this (seemingly working) without the `propagateASGTags` set to true, but that is something that I've seen have issue.
You can look at the autoscaler pod logs for information.

While the spawned containers (e.g., where you run your notebook) don't use these volumes, the hub will.
You can read about [gp2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html) class.
Note that we will be using [config-aws.yaml](aws/config-aws.yaml) if you don't need SSL, and [config-aws-ssl.yaml](aws/config-aws-ssl.yaml) if you do. For the latter, the jupyter spawner will generate let's encrypt certificates for us, given that we have correctly configured DNS.

### 2. Deploy JupyterHub

We will use [helm](https://helm.sh/docs/helm/helm_install/) to install charts and deploy.

```bash
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update
```

You can see the versions available:

```bash
helm search repo jupyterhub
```
```console
NAME                 	CHART VERSION	APP VERSION	DESCRIPTION                                       
bitnami/jupyterhub   	4.2.0        	4.0.2      	JupyterHub brings the power of notebooks to gro...
jupyterhub/jupyterhub	3.0.2        	4.0.2      	Multi-user Jupyter installation                   
jupyterhub/pebble    	1.0.1        	v2.3.1     	This Helm chart bootstraps Pebble: an ACME serv...
```

Note that chart versions don't always coincide with software (or "app") versions. At the time of writing this,
we are using the jupyterhub/jupyterhub	3.0.2/4.0.2 versions, and our container bases point to 3.0.2 tags for the
corresponding images. Next, see the values we can set, which likely will come from a config*.yaml that we will choose.

```bash
helm show values jupyterhub/jupyterhub
```

<details>

<summary>Example values for the jupyterhub helm chart</summary>

```console
# fullnameOverride and nameOverride distinguishes blank strings, null values,
# and non-blank strings. For more details, see the configuration reference.
fullnameOverride: ""
nameOverride:

# enabled is ignored by the jupyterhub chart itself, but a chart depending on
# the jupyterhub chart conditionally can make use this config option as the
# condition.
enabled:

# custom can contain anything you want to pass to the hub pod, as all passed
# Helm template values will be made available there.
custom: {}

# imagePullSecret is configuration to create a k8s Secret that Helm chart's pods
# can get credentials from to pull their images.
imagePullSecret:
  create: false
  automaticReferenceInjection: true
  registry:
  username:
  password:
  email:
# imagePullSecrets is configuration to reference the k8s Secret resources the
# Helm chart's pods can get credentials from to pull their images.
imagePullSecrets: []

# hub relates to the hub pod, responsible for running JupyterHub, its configured
# Authenticator class KubeSpawner, and its configured Proxy class
# ConfigurableHTTPProxy. KubeSpawner creates the user pods, and
# ConfigurableHTTPProxy speaks with the actual ConfigurableHTTPProxy server in
# the proxy pod.
hub:
  revisionHistoryLimit:
  config:
    JupyterHub:
      admin_access: true
      authenticator_class: dummy
  service:
    type: ClusterIP
    annotations: {}
    ports:
      nodePort:
    extraPorts: []
    loadBalancerIP:
  baseUrl: /
  cookieSecret:
  initContainers: []
  nodeSelector: {}
  tolerations: []
  concurrentSpawnLimit: 64
  consecutiveFailureLimit: 5
  activeServerLimit:
  deploymentStrategy:
    ## type: Recreate
    ## - sqlite-pvc backed hubs require the Recreate deployment strategy as a
    ##   typical PVC storage can only be bound to one pod at the time.
    ## - JupyterHub isn't designed to support being run in parallel. More work
    ##   needs to be done in JupyterHub itself for a fully highly available (HA)
    ##   deployment of JupyterHub on k8s is to be possible.
    type: Recreate
  db:
    type: sqlite-pvc
    upgrade:
    pvc:
      annotations: {}
      selector: {}
      accessModes:
        - ReadWriteOnce
      storage: 1Gi
      subPath:
      storageClassName:
    url:
    password:
  labels: {}
  annotations: {}
  command: []
  args: []
  extraConfig: {}
  extraFiles: {}
  extraEnv: {}
  extraContainers: []
  extraVolumes: []
  extraVolumeMounts: []
  image:
    name: jupyterhub/k8s-hub
    tag: "3.0.2"
    pullPolicy:
    pullSecrets: []
  resources: {}
  podSecurityContext:
    fsGroup: 1000
  containerSecurityContext:
    runAsUser: 1000
    runAsGroup: 1000
    allowPrivilegeEscalation: false
  lifecycle: {}
  loadRoles: {}
  services: {}
  pdb:
    enabled: false
    maxUnavailable:
    minAvailable: 1
  networkPolicy:
    enabled: true
    ingress: []
    egress: []
    egressAllowRules:
      cloudMetadataServer: true
      dnsPortsCloudMetadataServer: true
      dnsPortsKubeSystemNamespace: true
      dnsPortsPrivateIPs: true
      nonPrivateIPs: true
      privateIPs: true
    interNamespaceAccessLabels: ignore
    allowedIngressPorts: []
  allowNamedServers: false
  namedServerLimitPerUser:
  authenticatePrometheus:
  redirectToServer:
  shutdownOnLogout:
  templatePaths: []
  templateVars: {}
  livenessProbe:
    # The livenessProbe's aim to give JupyterHub sufficient time to startup but
    # be able to restart if it becomes unresponsive for ~5 min.
    enabled: true
    initialDelaySeconds: 300
    periodSeconds: 10
    failureThreshold: 30
    timeoutSeconds: 3
  readinessProbe:
    # The readinessProbe's aim is to provide a successful startup indication,
    # but following that never become unready before its livenessProbe fail and
    # restarts it if needed. To become unready following startup serves no
    # purpose as there are no other pod to fallback to in our non-HA deployment.
    enabled: true
    initialDelaySeconds: 0
    periodSeconds: 2
    failureThreshold: 1000
    timeoutSeconds: 1
  existingSecret:
  serviceAccount:
    create: true
    name:
    annotations: {}
  extraPodSpec: {}

rbac:
  create: true

# proxy relates to the proxy pod, the proxy-public service, and the autohttps
# pod and proxy-http service.
proxy:
  secretToken:
  annotations: {}
  deploymentStrategy:
    ## type: Recreate
    ## - JupyterHub's interaction with the CHP proxy becomes a lot more robust
    ##   with this configuration. To understand this, consider that JupyterHub
    ##   during startup will interact a lot with the k8s service to reach a
    ##   ready proxy pod. If the hub pod during a helm upgrade is restarting
    ##   directly while the proxy pod is making a rolling upgrade, the hub pod
    ##   could end up running a sequence of interactions with the old proxy pod
    ##   and finishing up the sequence of interactions with the new proxy pod.
    ##   As CHP proxy pods carry individual state this is very error prone. One
    ##   outcome when not using Recreate as a strategy has been that user pods
    ##   have been deleted by the hub pod because it considered them unreachable
    ##   as it only configured the old proxy pod but not the new before trying
    ##   to reach them.
    type: Recreate
    ## rollingUpdate:
    ## - WARNING:
    ##   This is required to be set explicitly blank! Without it being
    ##   explicitly blank, k8s will let eventual old values under rollingUpdate
    ##   remain and then the Deployment becomes invalid and a helm upgrade would
    ##   fail with an error like this:
    ##
    ##     UPGRADE FAILED
    ##     Error: Deployment.apps "proxy" is invalid: spec.strategy.rollingUpdate: Forbidden: may not be specified when strategy `type` is 'Recreate'
    ##     Error: UPGRADE FAILED: Deployment.apps "proxy" is invalid: spec.strategy.rollingUpdate: Forbidden: may not be specified when strategy `type` is 'Recreate'
    rollingUpdate:
  # service relates to the proxy-public service
  service:
    type: LoadBalancer
    labels: {}
    annotations: {}
    nodePorts:
      http:
      https:
    disableHttpPort: false
    extraPorts: []
    loadBalancerIP:
    loadBalancerSourceRanges: []
  # chp relates to the proxy pod, which is responsible for routing traffic based
  # on dynamic configuration sent from JupyterHub to CHP's REST API.
  chp:
    revisionHistoryLimit:
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    image:
      name: jupyterhub/configurable-http-proxy
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      tag: "4.5.6" # https://github.com/jupyterhub/configurable-http-proxy/tags
      pullPolicy:
      pullSecrets: []
    extraCommandLineFlags: []
    livenessProbe:
      enabled: true
      initialDelaySeconds: 60
      periodSeconds: 10
      failureThreshold: 30
      timeoutSeconds: 3
    readinessProbe:
      enabled: true
      initialDelaySeconds: 0
      periodSeconds: 2
      failureThreshold: 1000
      timeoutSeconds: 1
    resources: {}
    defaultTarget:
    errorTarget:
    extraEnv: {}
    nodeSelector: {}
    tolerations: []
    networkPolicy:
      enabled: true
      ingress: []
      egress: []
      egressAllowRules:
        cloudMetadataServer: true
        dnsPortsCloudMetadataServer: true
        dnsPortsKubeSystemNamespace: true
        dnsPortsPrivateIPs: true
        nonPrivateIPs: true
        privateIPs: true
      interNamespaceAccessLabels: ignore
      allowedIngressPorts: [http, https]
    pdb:
      enabled: false
      maxUnavailable:
      minAvailable: 1
    extraPodSpec: {}
  # traefik relates to the autohttps pod, which is responsible for TLS
  # termination when proxy.https.type=letsencrypt.
  traefik:
    revisionHistoryLimit:
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    image:
      name: traefik
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      tag: "v2.10.4" # ref: https://hub.docker.com/_/traefik?tab=tags
      pullPolicy:
      pullSecrets: []
    hsts:
      includeSubdomains: false
      preload: false
      maxAge: 15724800 # About 6 months
    resources: {}
    labels: {}
    extraInitContainers: []
    extraEnv: {}
    extraVolumes: []
    extraVolumeMounts: []
    extraStaticConfig: {}
    extraDynamicConfig: {}
    nodeSelector: {}
    tolerations: []
    extraPorts: []
    networkPolicy:
      enabled: true
      ingress: []
      egress: []
      egressAllowRules:
        cloudMetadataServer: true
        dnsPortsCloudMetadataServer: true
        dnsPortsKubeSystemNamespace: true
        dnsPortsPrivateIPs: true
        nonPrivateIPs: true
        privateIPs: true
      interNamespaceAccessLabels: ignore
      allowedIngressPorts: [http, https]
    pdb:
      enabled: false
      maxUnavailable:
      minAvailable: 1
    serviceAccount:
      create: true
      name:
      annotations: {}
    extraPodSpec: {}
  secretSync:
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    image:
      name: jupyterhub/k8s-secret-sync
      tag: "3.0.2"
      pullPolicy:
      pullSecrets: []
    resources: {}
  labels: {}
  https:
    enabled: false
    type: letsencrypt
    #type: letsencrypt, manual, offload, secret
    letsencrypt:
      contactEmail:
      # Specify custom server here (https://acme-staging-v02.api.letsencrypt.org/directory) to hit staging LE
      acmeServer: https://acme-v02.api.letsencrypt.org/directory
    manual:
      key:
      cert:
    secret:
      name:
      key: tls.key
      crt: tls.crt
    hosts: []

# singleuser relates to the configuration of KubeSpawner which runs in the hub
# pod, and its spawning of user pods such as jupyter-myusername.
singleuser:
  podNameTemplate:
  extraTolerations: []
  nodeSelector: {}
  extraNodeAffinity:
    required: []
    preferred: []
  extraPodAffinity:
    required: []
    preferred: []
  extraPodAntiAffinity:
    required: []
    preferred: []
  networkTools:
    image:
      name: jupyterhub/k8s-network-tools
      tag: "3.0.2"
      pullPolicy:
      pullSecrets: []
    resources: {}
  cloudMetadata:
    # block set to true will append a privileged initContainer using the
    # iptables to block the sensitive metadata server at the provided ip.
    blockWithIptables: true
    ip: 169.254.169.254
  networkPolicy:
    enabled: true
    ingress: []
    egress: []
    egressAllowRules:
      cloudMetadataServer: false
      dnsPortsCloudMetadataServer: true
      dnsPortsKubeSystemNamespace: true
      dnsPortsPrivateIPs: true
      nonPrivateIPs: true
      privateIPs: false
    interNamespaceAccessLabels: ignore
    allowedIngressPorts: []
  events: true
  extraAnnotations: {}
  extraLabels:
    hub.jupyter.org/network-access-hub: "true"
  extraFiles: {}
  extraEnv: {}
  lifecycleHooks: {}
  initContainers: []
  extraContainers: []
  allowPrivilegeEscalation: false
  uid: 1000
  fsGid: 100
  serviceAccountName:
  storage:
    type: dynamic
    extraLabels: {}
    extraVolumes: []
    extraVolumeMounts: []
    static:
      pvcName:
      subPath: "{username}"
    capacity: 10Gi
    homeMountPath: /home/jovyan
    dynamic:
      storageClass:
      pvcNameTemplate: claim-{username}{servername}
      volumeNameTemplate: volume-{username}{servername}
      storageAccessModes: [ReadWriteOnce]
  image:
    name: jupyterhub/k8s-singleuser-sample
    tag: "3.0.2"
    pullPolicy:
    pullSecrets: []
  startTimeout: 300
  cpu:
    limit:
    guarantee:
  memory:
    limit:
    guarantee: 1G
  extraResource:
    limits: {}
    guarantees: {}
  cmd: jupyterhub-singleuser
  defaultUrl:
  extraPodConfig: {}
  profileList: []

# scheduling relates to the user-scheduler pods and user-placeholder pods.
scheduling:
  userScheduler:
    enabled: true
    revisionHistoryLimit:
    replicas: 2
    logLevel: 4
    # plugins are configured on the user-scheduler to make us score how we
    # schedule user pods in a way to help us schedule on the most busy node. By
    # doing this, we help scale down more effectively. It isn't obvious how to
    # enable/disable scoring plugins, and configure them, to accomplish this.
    #
    # plugins ref: https://kubernetes.io/docs/reference/scheduling/config/#scheduling-plugins-1
    # migration ref: https://kubernetes.io/docs/reference/scheduling/config/#scheduler-configuration-migrations
    #
    plugins:
      score:
        # These scoring plugins are enabled by default according to
        # https://kubernetes.io/docs/reference/scheduling/config/#scheduling-plugins
        # 2022-02-22.
        #
        # Enabled with high priority:
        # - NodeAffinity
        # - InterPodAffinity
        # - NodeResourcesFit
        # - ImageLocality
        # Remains enabled with low default priority:
        # - TaintToleration
        # - PodTopologySpread
        # - VolumeBinding
        # Disabled for scoring:
        # - NodeResourcesBalancedAllocation
        #
        disabled:
          # We disable these plugins (with regards to scoring) to not interfere
          # or complicate our use of NodeResourcesFit.
          - name: NodeResourcesBalancedAllocation
          # Disable plugins to be allowed to enable them again with a different
          # weight and avoid an error.
          - name: NodeAffinity
          - name: InterPodAffinity
          - name: NodeResourcesFit
          - name: ImageLocality
        enabled:
          - name: NodeAffinity
            weight: 14631
          - name: InterPodAffinity
            weight: 1331
          - name: NodeResourcesFit
            weight: 121
          - name: ImageLocality
            weight: 11
    pluginConfig:
      # Here we declare that we should optimize pods to fit based on a
      # MostAllocated strategy instead of the default LeastAllocated.
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            resources:
              - name: cpu
                weight: 1
              - name: memory
                weight: 1
            type: MostAllocated
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    image:
      # IMPORTANT: Bumping the minor version of this binary should go hand in
      #            hand with an inspection of the user-scheduelrs RBAC resources
      #            that we have forked in
      #            templates/scheduling/user-scheduler/rbac.yaml.
      #
      #            Debugging advice:
      #
      #            - Is configuration of kube-scheduler broken in
      #              templates/scheduling/user-scheduler/configmap.yaml?
      #
      #            - Is the kube-scheduler binary's compatibility to work
      #              against a k8s api-server that is too new or too old?
      #
      #            - You can update the GitHub workflow that runs tests to
      #              include "deploy/user-scheduler" in the k8s namespace report
      #              and reduce the user-scheduler deployments replicas to 1 in
      #              dev-config.yaml to get relevant logs from the user-scheduler
      #              pods. Inspect the "Kubernetes namespace report" action!
      #
      #            - Typical failures are that kube-scheduler fails to search for
      #              resources via its "informers", and won't start trying to
      #              schedule pods before they succeed which may require
      #              additional RBAC permissions or that the k8s api-server is
      #              aware of the resources.
      #
      #            - If "successfully acquired lease" can be seen in the logs, it
      #              is a good sign kube-scheduler is ready to schedule pods.
      #
      name: registry.k8s.io/kube-scheduler
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow. The minor version is pinned in the
      # workflow, and should be updated there if a minor version bump is done
      # here. We aim to stay around 1 minor version behind the latest k8s
      # version.
      #
      tag: "v1.26.7" # ref: https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG
      pullPolicy:
      pullSecrets: []
    nodeSelector: {}
    tolerations: []
    labels: {}
    annotations: {}
    pdb:
      enabled: true
      maxUnavailable: 1
      minAvailable:
    resources: {}
    serviceAccount:
      create: true
      name:
      annotations: {}
    extraPodSpec: {}
  podPriority:
    enabled: false
    globalDefault: false
    defaultPriority: 0
    imagePullerPriority: -5
    userPlaceholderPriority: -10
  userPlaceholder:
    enabled: true
    image:
      name: registry.k8s.io/pause
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      # If you update this, also update prePuller.pause.image.tag
      #
      tag: "3.9"
      pullPolicy:
      pullSecrets: []
    revisionHistoryLimit:
    replicas: 0
    labels: {}
    annotations: {}
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    resources: {}
  corePods:
    tolerations:
      - key: hub.jupyter.org/dedicated
        operator: Equal
        value: core
        effect: NoSchedule
      - key: hub.jupyter.org_dedicated
        operator: Equal
        value: core
        effect: NoSchedule
    nodeAffinity:
      matchNodePurpose: prefer
  userPods:
    tolerations:
      - key: hub.jupyter.org/dedicated
        operator: Equal
        value: user
        effect: NoSchedule
      - key: hub.jupyter.org_dedicated
        operator: Equal
        value: user
        effect: NoSchedule
    nodeAffinity:
      matchNodePurpose: prefer

# prePuller relates to the hook|continuous-image-puller DaemonsSets
prePuller:
  revisionHistoryLimit:
  labels: {}
  annotations: {}
  resources: {}
  containerSecurityContext:
    runAsUser: 65534 # nobody user
    runAsGroup: 65534 # nobody group
    allowPrivilegeEscalation: false
  extraTolerations: []
  # hook relates to the hook-image-awaiter Job and hook-image-puller DaemonSet
  hook:
    enabled: true
    pullOnlyOnChanges: true
    # image and the configuration below relates to the hook-image-awaiter Job
    image:
      name: jupyterhub/k8s-image-awaiter
      tag: "3.0.2"
      pullPolicy:
      pullSecrets: []
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    podSchedulingWaitDuration: 10
    nodeSelector: {}
    tolerations: []
    resources: {}
    serviceAccount:
      create: true
      name:
      annotations: {}
  continuous:
    enabled: true
  pullProfileListImages: true
  extraImages: {}
  pause:
    containerSecurityContext:
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
    image:
      name: registry.k8s.io/pause
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      # If you update this, also update scheduling.userPlaceholder.image.tag
      #
      tag: "3.9"
      pullPolicy:
      pullSecrets: []

ingress:
  enabled: false
  annotations: {}
  ingressClassName:
  hosts: []
  pathSuffix:
  pathType: Prefix
  tls: []

# cull relates to the jupyterhub-idle-culler service, responsible for evicting
# inactive singleuser pods.
#
# The configuration below, except for enabled, corresponds to command-line flags
# for jupyterhub-idle-culler as documented here:
# https://github.com/jupyterhub/jupyterhub-idle-culler#as-a-standalone-script
#
cull:
  enabled: true
  users: false # --cull-users
  adminUsers: true # --cull-admin-users
  removeNamedServers: false # --remove-named-servers
  timeout: 3600 # --timeout
  every: 600 # --cull-every
  concurrency: 10 # --concurrency
  maxAge: 0 # --max-age

debug:
  enabled: false

global:
  safeToShowValues: false
```

</details>

#### Changes You Might Need to Make:

- Change the config*.yaml image-> name and tag that you deploy to use your images.
- You might want to change the number of user placeholder pods
- Also change the hub->concurrentSpawnLimit
- Change the password, ssl secret, and domain name if applicable
- Change the aws/eksctl-config.yaml autoscaling ranges depending on your needs.
- Remove pullPolicy Always if you don't expect to want to update/re-pull an image every time (ideal for production)

And here is how to deploy, assuming the default namespace. Please choose your cloud appropriately!

```bash
# This is for Google Cloud
helm install flux-jupyter jupyterhub/jupyterhub --values gcp/config.yaml

# This is for Amazon EKS without SSL
helm install flux-jupyter jupyterhub/jupyterhub --values aws/config-aws.yaml

# This is for Amazon EKS with SSL (assuming DNS is configured)
helm install flux-jupyter jupyterhub/jupyterhub --values aws/config-aws-ssl.yaml
```

If you're configuring SSL, you will need to get the service DNS name after creation. With that name you can assign a CNAME as appropriate. Then delete the `autohttps` pod, which triggers a pod recreation and certificate generation.

If you mess something up, you can change the file and run `helm upgrade`:

```bash
helm upgrade flux-jupyter jupyterhub/jupyterhub --values aws/config-aws-ssl.yaml
```

If you REALLY mess something up, you can tear the whole thing down and then install again:

```bash
helm uninstall flux-jupyter
```

Note that in practice of bringing this up and down many times, we have seen the proxy-public
not create a handful of times. If this happens, just tear down everything, wait for all pods
to terminate, and then start freshly. When you run a command, also note that the terminal will hang!
You can see progress in another terminal:

```bash
$ kubectl get pods
```

or try watching:

```bash
$ kubectl get pods --watch
```

When it's done, you should see:

```bash
$ kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
continuous-image-puller-nvr4g     1/1     Running   0          5m31s
hub-7d59dfb748-mrfdv              1/1     Running   0          5m31s
proxy-d9dfbf77b-v488t             1/1     Running   0          5m31s
user-scheduler-587fcc5479-c4mmk   1/1     Running   0          5m31s
user-scheduler-587fcc5479-x6jmk   1/1     Running   0          5m31s
```

(The numbers of each above might vary based on the size of your cluster). And the terminal provides a lot of useful output:

<details>

<summary>Output of Terminal on Completed Install</summary>

```console
NAME: flux-jupyter
LAST DEPLOYED: Sun Aug 27 15:00:15 2023
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
.      __                          __                  __  __          __
      / / __  __  ____    __  __  / /_  ___    _____  / / / / __  __  / /_
 __  / / / / / / / __ \  / / / / / __/ / _ \  / ___/ / /_/ / / / / / / __ \
/ /_/ / / /_/ / / /_/ / / /_/ / / /_  /  __/ / /    / __  / / /_/ / / /_/ /
\____/  \__,_/ / .___/  \__, /  \__/  \___/ /_/    /_/ /_/  \__,_/ /_.___/
              /_/      /____/

       You have successfully installed the official JupyterHub Helm chart!

### Installation info

  - Kubernetes namespace: default
  - Helm release name:    flux-jupyter
  - Helm chart version:   3.0.2
  - JupyterHub version:   4.0.2
  - Hub pod packages:     See https://github.com/jupyterhub/zero-to-jupyterhub-k8s/blob/3.0.2/images/hub/requirements.txt

### Followup links

  - Documentation:  https://z2jh.jupyter.org
  - Help forum:     https://discourse.jupyter.org
  - Social chat:    https://gitter.im/jupyterhub/jupyterhub
  - Issue tracking: https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues

### Post-installation checklist

  - Verify that created Pods enter a Running state:

      kubectl --namespace=default get pod

    If a pod is stuck with a Pending or ContainerCreating status, diagnose with:

      kubectl --namespace=default describe pod <name of pod>

    If a pod keeps restarting, diagnose with:

      kubectl --namespace=default logs --previous <name of pod>

  - Verify an external IP is provided for the k8s Service proxy-public.

      kubectl --namespace=default get service proxy-public

    If the external ip remains <pending>, diagnose with:

      kubectl --namespace=default describe service proxy-public

  - Verify web based access:

    You have not configured a k8s Ingress resource so you need to access the k8s
    Service proxy-public directly.

    If your computer is outside the k8s cluster, you can port-forward traffic to
    the k8s Service proxy-public with kubectl to access it from your
    computer.

      kubectl --namespace=default port-forward service/proxy-public 8080:http

    Try insecure HTTP access: http://localhost:8080
```

</details>

### 3. Get Public Proxy

Then to find the public proxy:

```bash
kubectl get service proxy-public
```
```console
NAME           TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
proxy-public   LoadBalancer   10.96.179.168   <pending>     80:32530/TCP   7m22s
```
or:

```bash
kubectl get service proxy-public --output jsonpath='{.status.loadBalancer.ingress[].ip}'
```

Note that for Google, it looks like an ip address. For aws you get a string monster!

```console
a054af2758c1549f780a433e5515a9d4-1012389935.us-east-2.elb.amazonaws.com
```

This might take a minute to fully be there - if it doesn't work immediately give it that.
At this point, you should be able to login as any user, open the notebook (nested two levels)
and interact with Flux! Remember that if you don't see the service, try deleting everything and
starting fresh. If that doesn't work, there might be some new error we didn't anticipate,
and you can look at logs.

### Clean up

For both:

```bash
helm uninstall flux-jupyter
```

For Google Cloud:

```bash
gcloud container clusters delete flux-jupyter
```

For AWS:

```bash
# If you don't do this first, it will tell the pods are un-evictable and loop forever
$ kubectl delete pod --all-namespaces --all --force
# Then delete the cluster
$ eksctl delete cluster --config-file aws/eksctl-config.yaml --wait
```

In practice, you'll need to start deleting with `eksctl` and then you will see the pod eviction warning
(because they were re-created) and you'll need to run the command again, and then it will clean up.

### Tutorial "would be nice" additions

- Flux accounting
 - after flux resource list, to see queues available (flux queue list)
 - how to specify a bank for a job 
 - list banks (all) - flux account view-bank --tree
 - specify banks - flux account view user $USER
