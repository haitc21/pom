#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
output="${repo_root}/deploy/demo/holmesgpt/kubeconfig"
context="${K8S_CONTEXT:-kubernetes-admin@kubernetes}"
namespace="${K8S_NAMESPACE:-holmesgpt}"
service_account="${K8S_SERVICE_ACCOUNT:-holmesgpt-readonly}"

command -v kubectl >/dev/null || { echo "kubectl is required" >&2; exit 1; }
kubectl config get-contexts "$context" >/dev/null 2>&1 || {
  echo "Kubernetes context '$context' was not found" >&2
  exit 1
}

kubectl -n "$namespace" get serviceaccount "$service_account" >/dev/null 2>&1 || {
  echo "ServiceAccount '$service_account' was not found in namespace '$namespace'; apply holmesgpt/readonly-rbac.yaml first" >&2
  exit 1
}
if kubectl auth can-i create deployments --as="system:serviceaccount:${namespace}:${service_account}" >/dev/null 2>&1; then
  echo "ServiceAccount unexpectedly has deployment write permission" >&2
  exit 1
fi
if ! kubectl auth can-i get pods --as="system:serviceaccount:${namespace}:${service_account}" >/dev/null 2>&1; then
  echo "ServiceAccount cannot read pods" >&2
  exit 1
fi

server=$(kubectl config view --raw --minify --context "$context" -o jsonpath='{.clusters[0].cluster.server}')
ca_data=$(kubectl config view --raw --minify --context "$context" -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
token=$(kubectl -n "$namespace" create token "$service_account" --duration=24h)

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
cat > "$tmp" <<EOF
apiVersion: v1
kind: Config
clusters:
- name: aic-k8s
  cluster:
    server: ${server}
    certificate-authority-data: ${ca_data}
contexts:
- name: aic-k8s
  context:
    cluster: aic-k8s
    namespace: ${namespace}
    user: ${service_account}
current-context: aic-k8s
users:
- name: ${service_account}
  user:
    token: ${token}
EOF
test -s "$tmp"
install -m 0600 "$tmp" "$output"
echo "Wrote read-only mounted kubeconfig: $output"
