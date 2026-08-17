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
- Redmine and PostOps Memory integration are out of scope for this infrastructure test.

To remove only the nginx smoke test:

```bash
kubectl delete namespace poc-web
kubectl delete namespace ingress-nginx
```
