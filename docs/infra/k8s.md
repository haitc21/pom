# Kubernetes PoC infrastructure

Status: deployed and verified on 2026-08-17.

## Scope and topology

- Three new Ubuntu 24.04.4 KVM/libvirt VMs: `k8s01` (control-plane), `k8s02` and `k8s03` (workers).
- Existing `controller`, `compute01`, and `compute02` VMs were not modified.
- Kubernetes `v1.35.7`, kubeadm/kubelet/kubectl; containerd `2.2.1` with `SystemdCgroup=true`.
- Calico `v3.30.3`, VXLAN, pod CIDR `10.244.0.0/16`; service CIDR `10.96.0.0/12`.
- VM resources: `k8s01` 2 vCPU/6 GiB/50 GiB; workers 2 vCPU/4 GiB/40 GiB.
- Disks: `/data/k8s-poc/images/k8s01.qcow2`, `k8s02.qcow2`, `k8s03.qcow2`.

## Network

Persistent VM-only libvirt network `postops-k8s`:

```xml
<network>
  <name>postops-k8s</name>
  <forward mode='none'/>
  <bridge name='virbr-k8s' stp='on' delay='0'/>
  <ip address='10.77.0.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.77.0.100' end='10.77.0.200'/>
      <host mac='52:54:00:77:01:01' name='k8s01' ip='10.77.0.11'/>
      <host mac='52:54:00:77:01:02' name='k8s02' ip='10.77.0.12'/>
      <host mac='52:54:00:77:01:03' name='k8s03' ip='10.77.0.13'/>
    </dhcp>
  </ip>
</network>
```

The temporary `default` NAT interface was used only to bootstrap and pull images, then detached. Final VM interfaces are `postops-k8s` only; external access from guests is intentionally unavailable.

## Access

```bash
ssh devops@10.77.0.11   # control-plane
ssh devops@10.77.0.12   # worker
ssh devops@10.77.0.13   # worker
```

On `k8s01`, `/home/devops/.kube/config` is installed as the default kubeconfig:

```bash
kubectl get nodes -o wide
```

Expected result: all three nodes `Ready`, Kubernetes `v1.35.7`, runtime `containerd://2.2.1`.

## Nginx and Ingress smoke test

The test namespace is `poc-web`. The following manifest was applied:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: poc-web
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  namespace: poc-web
spec:
  replicas: 2
  selector:
    matchLabels: {app: nginx}
  template:
    metadata:
      labels: {app: nginx}
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - name: http
              containerPort: 80
          readinessProbe:
            httpGet: {path: /, port: http}
            initialDelaySeconds: 2
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: nginx
  namespace: poc-web
spec:
  selector: {app: nginx}
  ports:
    - name: http
      port: 80
      targetPort: http
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx
  namespace: poc-web
spec:
  ingressClassName: nginx
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx
                port: {number: 80}
```

Ingress-nginx `v1.12.1` was installed from the official bare-metal manifest and scaled to two controller replicas, one per worker. Its HTTP NodePort is `30553`.

Browser checks from the host succeeded:

- http://10.77.0.12:30553/
- http://10.77.0.13:30553/

Both returned the nginx welcome page. The two application pods were scheduled on `k8s02` and `k8s03`; deleting one pod caused a healthy replacement and both Service endpoints remained ready.

No separate load-balancer VM is required for this isolated PoC. For production, place HAProxy/nginx or an external load balancer in front of the worker NodePorts.

## Verification and cleanup

- Calico node/controller pods and CoreDNS were `Running`.
- `k8s01` reboot recovery returned all nodes to `Ready`.
- Disposable negative-path workloads were removed; no `poc-test` namespace remains.
- The retained resources are the three VMs, their disks, and `postops-k8s`.
- Redmine and AI Incident Copilot (AIC) integration are out of scope for this infrastructure test.

## NFS persistent storage

Created an additional VM for shared storage:

- VM: `k8s-storage`, Ubuntu 24.04.4, 2 vCPU, 4 GiB RAM
- IP: `10.77.0.14` on `postops-k8s`
- OS disk: `/data/k8s-poc/images/k8s-storage.qcow2` (20 GiB)
- Data disk: `/data/k8s-poc/images/k8s-storage-data.qcow2` (100 GiB)
- NFS v4 export: `10.77.0.14:/srv/nfs/k8s`, backed by `/dev/vdb` mounted at `/srv/nfs/k8s`
- Export access is restricted to `10.77.0.0/24`; the final VM has no NAT interface.

The Kubernetes cluster was connected using `nfs-subdir-external-provisioner` in namespace `storage-system`:

- StorageClass: `nfs-client`
- Provisioner: `k8s-sigs.io/nfs-subdir-external-provisioner`
- Dynamic PVCs use RWX subdirectories under the NFS export.

Verification passed with a disposable `storage-test` namespace: a 1 GiB RWX PVC reached `Bound`, a pod on `k8s02` mounted it, wrote `verification.txt`, and the file was read back from `k8s-storage`. The namespace and test PV were then deleted. The StorageClass and provisioner remain installed.

The host has `nfs-common` installed and `/data/k8s-poc/storage` is mounted persistently with an `/etc/fstab` entry:

```bash
mount -t nfs4 -o vers=4 10.77.0.14:/srv/nfs/k8s /data/k8s-poc/storage
```

The mount was verified by writing `host-mount-verification.txt` on the host and reading it back from `k8s-storage`. The authoritative persistent data path for Kubernetes is the NFS export on `k8s-storage`; its backing qcow2 data disk is stored under `/data/k8s-poc/images/`.

### Installation procedure

The following is the reproducible sequence used for the storage integration. Bootstrap-only NAT interfaces must be removed again before acceptance verification.

1. Create the storage VM disks on the host. The OS disk uses the verified Ubuntu 24.04 cloud image; the second disk is the NFS data disk:

   ```bash
   qemu-img create -f qcow2 -F qcow2 \
     -b /data/k8s-poc/ubuntu-24.04-cloudimg-amd64.img \
     /data/k8s-poc/images/k8s-storage.qcow2 20G
   qemu-img create -f qcow2 \
     /data/k8s-poc/images/k8s-storage-data.qcow2 100G
   ```

2. Define and boot `k8s-storage` with 2 vCPU, 4 GiB RAM, both disks, a temporary `default` NAT NIC, and the persistent `postops-k8s` NIC (`10.77.0.14`). Use NoCloud metadata to create the `devops` account and configure the static network address. Do not store the password or seed contents in this repository.

3. On `k8s-storage`, install and configure NFS. `/dev/vdb` is formatted once, mounted persistently, and exported only to the Kubernetes subnet:

   ```bash
   sudo apt-get update
   sudo apt-get install -y nfs-kernel-server nfs-common
   sudo mkfs.ext4 /dev/vdb                 # only for a new empty data disk
   sudo mkdir -p /srv/nfs/k8s
   echo '/dev/vdb /srv/nfs/k8s ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
   sudo mount -a
   sudo chown nobody:nogroup /srv/nfs/k8s
   sudo chmod 0777 /srv/nfs/k8s
   echo '/srv/nfs/k8s 10.77.0.0/24(rw,sync,no_subtree_check,no_root_squash)' | sudo tee /etc/exports
   sudo exportfs -rav
   sudo systemctl enable --now nfs-kernel-server
   ```

4. Install the NFS client helper on every Kubernetes worker. The workers require `nfs-common` because kubelet performs the NFS mount:

   ```bash
   sudo apt-get update
   sudo apt-get install -y nfs-common
   ```

5. Install `nfs-subdir-external-provisioner` from its upstream deployment files. Set `NFS_SERVER=10.77.0.14`, `NFS_PATH=/srv/nfs/k8s`, and deploy it in `storage-system`. Apply its RBAC, Deployment, and StorageClass resources, then wait for the provisioner rollout:

   ```bash
   kubectl create namespace storage-system
   kubectl apply -f nfs-provisioner-rbac.yaml
   kubectl apply -f nfs-provisioner-deployment.yaml
   kubectl apply -f nfs-provisioner-class.yaml
   kubectl rollout status deployment/nfs-client-provisioner \
     -n storage-system --timeout=120s
   ```

6. Install the NFS client package on the host and mount the export persistently:

   ```bash
   sudo apt-get install -y nfs-common
   sudo mkdir -p /data/k8s-poc/storage
   echo '10.77.0.14:/srv/nfs/k8s /data/k8s-poc/storage nfs4 _netdev,nofail,x-systemd.automount,vers=4 0 0' \
     | sudo tee -a /etc/fstab
   sudo mount /data/k8s-poc/storage
   ```

7. Verify dynamic provisioning with a disposable RWX PVC and pod. Confirm the PVC is `Bound`, the pod can write/read a file, and the file exists below `/srv/nfs/k8s` on the storage VM. Delete the test namespace afterward so no test PV remains.

8. Detach every temporary `default` NAT NIC from `k8s-storage` and the workers. Restore the internal route via `10.77.0.1`, then verify that the three Kubernetes nodes remain `Ready`, the NFS provisioner remains `Running`, and `nfs-client` is still present.

## Observability stack

The observability stack was installed with Helm on 2026-08-17. Helm CLI `v4.2.4` was installed on the host; the binary and chart caches are host-local and are not part of the repository.

### Components and versions

- `prometheus-community/kube-prometheus-stack` chart `88.3.0` (Prometheus `v3.13.2`, Grafana `13.1.3`, Alertmanager `v0.33.1`, node-exporter and kube-state-metrics).
- `grafana-community/loki` chart `18.9.0`, Loki `3.7.6`, deployment mode `Monolithic`, one replica.
- `grafana/alloy` chart `1.11.1`, Alloy `v1.18.1`, one Deployment replica collecting Kubernetes pod logs through the Kubernetes API.
- All persistent claims use StorageClass `nfs-client`: Prometheus 10 GiB, Loki 20 GiB, Grafana 5 GiB, Alertmanager 2 GiB.
- Prometheus retention is 3 days; Loki retention is 7 days.

### Installation procedure

1. Add and update the upstream repositories:

   ```bash
   export PATH=/home/haitc/.local/bin:$PATH
   export KUBECONFIG=/tmp/k8s-admin.conf  # copied securely from k8s01; never commit it
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo add grafana-community https://grafana-community.github.io/helm-charts
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   ```

2. Create the monitoring namespace and a Grafana admin Secret outside the repository. The password is generated locally and must not be written to documentation:

   ```bash
   kubectl create namespace monitoring
   kubectl -n monitoring create secret generic grafana-admin \
     --from-literal=admin-user=admin \
     --from-literal=admin-password="$(openssl rand -hex 24)"
   ```

3. Install `kube-prometheus-stack` using values that enable NFS-backed persistence, set Prometheus retention to `3d`, and expose Grafana as NodePort `30030`:

   ```bash
   helm install monitoring prometheus-community/kube-prometheus-stack \
     --version 88.3.0 -n monitoring -f kube-prometheus-values.yaml --wait
   ```

4. Install Loki in monolithic mode. Disable the default memcached chunk/results caches because their default memory requests exceed the available worker capacity in this 14 GiB cluster:

   ```bash
   helm install loki grafana-community/loki \
     --version 18.9.0 -n loki --create-namespace -f loki-values.yaml --wait
   ```

5. Install Alloy with a Kubernetes service account that discovers pod targets, tails their logs through the API, and sends them to the Loki gateway:

   ```bash
   helm install alloy grafana/alloy \
     --version 1.11.1 -n loki -f alloy-values.yaml --wait
   ```

6. Add Loki as a Grafana datasource and upgrade the monitoring release:

   ```bash
   helm upgrade monitoring prometheus-community/kube-prometheus-stack \
     --version 88.3.0 -n monitoring \
     -f kube-prometheus-values.yaml \
     -f kube-prometheus-loki-datasource.yaml --wait
   ```

The temporary values files used by the commands above contained the following settings (they were deliberately kept out of Git because they are deployment inputs, not application source):

```yaml
# kube-prometheus-values.yaml (key settings)
grafana:
  admin:
    existingSecret: grafana-admin
  persistence:
    enabled: true
    type: sts
    storageClassName: nfs-client
    size: 5Gi
  service:
    type: NodePort
    nodePort: 30030
prometheus:
  prometheusSpec:
    retention: 3d
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: nfs-client
          accessModes: [ReadWriteOnce]
          resources:
            requests: {storage: 10Gi}
alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: nfs-client
          accessModes: [ReadWriteOnce]
          resources:
            requests: {storage: 2Gi}
```

```yaml
# loki-values.yaml (key settings)
deploymentMode: Monolithic
loki:
  auth_enabled: false
  commonConfig: {replication_factor: 1}
  storage: {type: filesystem}
  schemaConfig:
    configs:
      - from: "2024-04-01"
        store: tsdb
        object_store: filesystem
        schema: v13
        index: {prefix: index_, period: 24h}
  limits_config: {retention_period: 168h}
singleBinary:
  replicas: 1
  persistence:
    enabled: true
    storageClass: nfs-client
    size: 20Gi
chunksCache: {enabled: false}
resultsCache: {enabled: false}
lokiCanary: {enabled: false}
gateway: {enabled: true}
```

```yaml
# alloy-values.yaml (key settings)
controller:
  type: deployment
  replicas: 1
alloy:
  configMap:
    content: |
      discovery.kubernetes "pods" {
        role = "pod"
      }
      loki.source.kubernetes "pods" {
        targets = discovery.kubernetes.pods.targets
        forward_to = [loki.write.endpoint.receiver]
      }
      loki.write "endpoint" {
        endpoint {
          url = "http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push"
          tenant_id = "local"
        }
      }
```

The datasource overlay used by the final `helm upgrade` was:

```yaml
grafana:
  additionalDataSources:
    - name: Loki
      type: loki
      access: proxy
      url: http://loki-gateway.loki.svc.cluster.local
      isDefault: false
```

7. During image/chart downloads, a temporary `default` NAT NIC may be attached to the three Kubernetes VMs. Configure a temporary route through `192.168.122.1`, then restore the internal route and detach those NICs after all pods are ready. The final VM interfaces remain `postops-k8s` only.

### Verification

- Prometheus `/api/v1/query?query=up` returned successful Kubernetes `up` metrics.
- Loki labels and LogQL queries returned logs forwarded by Alloy, including the Alloy-to-Loki gateway request stream.
- Grafana `/api/health` returned `database: ok` through both worker NodePorts:
  - `http://10.77.0.12:30030/`
  - `http://10.77.0.13:30030/`
- Grafana datasource configuration contains both Prometheus and `http://loki-gateway.loki.svc.cluster.local`.
- All observability pods were `Running`; all four observability PVCs were `Bound` via `nfs-client`.
- After NAT removal, all three Kubernetes nodes remained `Ready` and the host NFS mount remained active.

Retrieve the generated Grafana password only when needed:

```bash
kubectl -n monitoring get secret grafana-admin \
  -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

To remove only the nginx smoke test:

```bash
kubectl delete namespace poc-web
kubectl delete namespace ingress-nginx
```

The initial `poc-web` nginx smoke-test namespace has been removed. The `ingress-nginx` controller remains installed as shared cluster ingress infrastructure for subsequent applications.

## Nginx load-balancer VM

For convenient browser access, `k8s-lb` is a small Ubuntu 24.04 VM running Nginx:

- VM: `k8s-lb`, 1 vCPU, 1 GiB RAM, 12 GiB qcow2 disk
- IP: `10.77.0.15` on the internal `postops-k8s` network only
- Disk: `/data/k8s-poc/images/k8s-lb.qcow2`
- Login: `devops` (the same lab password used for the other VMs)
- Nginx upstreams: workers `10.77.0.12` and `10.77.0.13`

Routing configured on the VM:

- `http://poc.k8s.local/` (or any unmatched host) -> ingress-nginx NodePort `30553`
- `http://grafana.k8s.local/` -> Grafana NodePort `30030`

The host resolves these names through `/etc/hosts`:

```text
10.77.0.15 k8s-lb k8s-lb.local grafana.k8s.local poc.k8s.local
```

Verification from the host:

```bash
curl --noproxy '*' http://grafana.k8s.local/api/health
curl --noproxy '*' http://poc.k8s.local/
```

The temporary `default` NAT interface used to install packages was detached after setup; the VM now has only the internal interface.

### Grafana/PostgreSQL storage note (PoC)

Grafana is intentionally a single replica. Its database is PostgreSQL 16 on `k8s-storage` (`10.77.0.14`) using the VM's normal filesystem; no dedicated PostgreSQL disk or HA database is used for this HolmesGPT PoC. Grafana persistence is disabled, so it does not use the NFS PVC for SQLite. The PostgreSQL database/user are `grafana` and the Kubernetes Secret `monitoring/grafana-postgres` supplies the connection password. The original NFS PVC is retained as a rollback artifact.

Because the lab network does not advertise Calico pod CIDRs to the storage VM, routes for the current pod ranges (`10.244.235.0/24`, `10.244.236.0/24`, `10.244.237.0/24`) were added on `k8s-storage`; these are PoC runtime routes and should be replaced by proper routed networking if the environment is rebuilt.

Prometheus remains a single replica for the PoC. Loki continues to use the NFS-backed storage; no monitoring HA or storage replication is in scope.

## HolmesGPT

Reproducible Helm values and credential templates are kept under [`deploy/k8s/`](/home/haitc/project/pom/deploy/k8s/):

- [`values/holmesgpt.yaml`](/home/haitc/project/pom/deploy/k8s/values/holmesgpt.yaml)
- [`values/monitoring.yaml`](/home/haitc/project/pom/deploy/k8s/values/monitoring.yaml)
- [`values/loki.yaml`](/home/haitc/project/pom/deploy/k8s/values/loki.yaml)
- Secret templates under [`deploy/k8s/secrets/`](/home/haitc/project/pom/deploy/k8s/secrets/); replace placeholders locally and never commit populated copies.

The install order and pinned chart versions are documented in [`deploy/k8s/README.md`](/home/haitc/project/pom/deploy/k8s/README.md). The values reproduce the current PoC sizing and read-only HolmesGPT RBAC; they do not include credentials.

When the Kubernetes deployment has at least one replica, HolmesGPT can be accessed through the existing `k8s-lb` without port-forwarding. As of 2026-08-19 the deployment is intentionally scaled to `0` during the Docker Compose transition, so this legacy endpoint is currently unavailable:

```bash
kubectl apply -f deploy/k8s/holmesgpt-ingress.yaml
echo '10.77.0.15 holmesgpt.k8s.local' | sudo tee -a /etc/hosts
curl --noproxy '*' http://holmesgpt.k8s.local/api/health
```

The Ingress uses ingress-nginx NodePort `30553`; the LB's default virtual host forwards unmatched hostnames to that NodePort.

### HolmesGPT CLI on the host

The host has HolmesGPT CLI `0.39.0` installed with `uv` using the existing Python 3.12 runtime. Its model configuration is stored in `~/.holmes/model_list.yaml` and points to the same LiteLLM model as the cluster. The API key is intentionally not stored in that file.

Run it by exporting only the key from the existing LibreChat `.env` (do not source the whole file because it contains shell-incompatible values):

```bash
export LITELLM_API_KEY="$(sed -n 's/^LITELLM_API_KEY=//p' ~/project/LibreChat/.env | sed 's/^"//; s/"$//')"
holmes ask --model mistral-3.5 --no-interactive \
  'Liệt kê các node Kubernetes và trạng thái Ready của chúng.'
```

The CLI uses the host's `~/.kube/config`, so it can inspect Kubernetes directly. Optional integrations that are not installed on the host may show as unavailable; the Kubernetes core/logs and Helm toolsets are available.

HolmesGPT `0.39.0` is installed with Helm release `holmesgpt` in namespace `holmesgpt`:

- Service: `holmesgpt-holmes` (ClusterIP, port 80 -> container port 5050)
- Desired Helm configuration: 1 replica pinned to `k8s02`; current runtime state: scaled to `0` for the Docker Compose transition
- Model gateway: LiteLLM-compatible endpoint `https://llmpipe.vnpost.vn/v1`
- Model label: `mistral-3.5` (`openai/mistral-3.5`)
- Enabled toolsets: Kubernetes core/logs, kube-prometheus-stack, Prometheus metrics, Loki logs
- Disabled: Internet, Bash, Robusta, Skills, Connectivity Check and all remediation/write actions
- RBAC: generated ClusterRole contains only `get`, `list`, and `watch` verbs; deleting pods is denied
- `CLUSTER_NAME=k8s-poc` is set so toolset status synchronization can identify the cluster.
- Loki toolset uses the built-in `grafana/loki` definition with `api_url=http://loki-gateway.loki.svc.cluster.local`.
- LiteLLM cost-map network lookup is disabled; model token limits are explicitly set for the configured gateway model.

The cluster has no general Internet egress. To reach LiteLLM, `k8s02` uses a temporary NAT interface with a single host route to the resolved LiteLLM address; its default route remains the internal `postops-k8s` gateway. The route is currently ephemeral and must be made persistent or replaced with an approved internal egress proxy before treating this as production-like infrastructure.

Historical validation was performed through a local port-forward while the Kubernetes replica was running:

```bash
kubectl -n holmesgpt port-forward svc/holmesgpt-holmes 18080:80
curl -H 'Content-Type: application/json' \
  -d '{"ask":"List the Kubernetes nodes and report their readiness status.","model":"mistral-3.5"}' \
  http://127.0.0.1:18080/api/chat
```

The Kubernetes investigation returned all three nodes as `Ready`. The previous missing-cluster and invalid-Loki-toolset warnings were corrected. The Helm release remains installed, but its deployment is currently scaled to `0`; do not expect the Service, Ingress or port-forward examples above to answer until a replica is restored.
