# Flux + Jupyter via KubeSpawner

Pre-requisites:

 - kubectl installed locally
 - A cloud with a Kubernetes cluster deployed

## Local Development

### 0. Build Images

Let's build a set of images - one spawner and one hub.

```bash
docker build --build-arg GLOBAL_PASSWORD=<password of your choice> -t <desired image name> -f Dockerfile.hub .
docker build -t <desired image name> -f Dockerfile.spawn .
```

And be sure to push your images to a public registry (or load them locally to your development cluster).


### 1. Deploy Cluster

#### Google Cloud

Here is how to create the cluster on Google Cloud using gcloud (and assuming you have logged in):

```bash
export GOOGLE_PROJECT=myproject
gcloud container clusters create flux-jupyter --project $GOOGLE_PROJECT \
    --zone us-central1-a --machine-type n1-standard-2 \
    --num-nodes=4 --enable-network-policy --enable-intra-node-visibility
```

#### AWS

I originally was going to follow the instructions [here](https://z2jh.jupyter.org/en/stable/kubernetes/amazon/step-zero-aws-eks.html) but then I decided I wanted to live, so I found an eksctl way to do it instead. :)
Here is how to create an equivalent cluster on AWS (EKS).

```bash
$ eksctl create cluster --config-file aws/eksctl-config.yaml 
```

Then generate a secret token - we will add this to [config-aws.yaml](config-aws.yaml)
This will deploy an EBS CSI driver:

```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
```

And you can read about [gp2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html) class.
Finally, we need to ask aws to generate us a [certificate](https://aws.amazon.com/certificate-manager/). See the [config-aws.yaml](config-aws.yaml) links for more detail, and [this blog post](https://www.arhea.net/posts/2020-06-18-jupyterhub-amazon-eks) that I created my configs from.

### 2. Deploy JupyterHub

We store Kubernetes manifests (the yaml files) alongside the repository since the helm charts are subject to change. Here is how we originally generated them.

```bash
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update
```

See the values we can set, which likely will come from the [config.yaml](config.yaml).

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
    ## - JupyterHub isn't designed to support being run in parallell. More work
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

And here is how to deploy, assuming the default namespace. Please choose your cloud appropriately!

```bash
# This is for Google Cloud
helm install flux-jupyter jupyterhub/jupyterhub --values config.yaml

# This is for Amazon EKS
helm install flux-jupyter jupyterhub/jupyterhub --values config-aws.yaml
```

That command will hang (it takes a while) but you can see progress in another terminal:

```bash
$ kubectl get pods
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

To run the AWS tutorial, visit https://tutorial.flux-framework.org 
You can use any login you want, but choose something relatvely uncommon 
(like your email address) or you may end up sharing a JupyterLab 
instance with another user. The tutorial password will be provided to you. 


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

It also (previously) told us we could get the insecure http access on localhost.
At this point, you should be able to login as any user, open the notebook (nested two levels)
and interact with Flux!

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
$ eksctl delete cluster --config-file aws/eksctl-config.yaml 
```


## Local

If you have Docker available, you can build and run the tutorial with:

```bash
docker build --build-arg GLOBAL_PASSWORD=<password of your choice> -t <desired image name> -f Dockerfile.hub .
docker build -t <desired image name> -f Dockerfile.spawn .
# You will need to change the spawner image name (`c.DockerSpawner.image`) in 
# jupyterhub_config.py to the name you chose.
# Create the jupyter network in Docker:
docker network create jupyterhub
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock --net jupyterhub --name jupyterhub -p 8000:8000 <hub image name>
```
Then you can point your browser to https://localhost:8000. You will need 
to override your browser's warning about the certificate in this configuration, too.

