FROM us-central1-docker.pkg.dev/genuine-flight-317411/mcp/kubernetes-remediation-mcp:1.1.0

# HolmesGPT 0.39 annotates an approved MCP invocation with this internal flag.
# The upstream remediation MCP 1.1.0 validates its tool schema strictly, so
# accept and ignore the marker before executing the existing allow-listed code.
USER root
COPY patch_approval_marker.py /tmp/patch_approval_marker.py
RUN python /tmp/patch_approval_marker.py && rm /tmp/patch_approval_marker.py
USER 1000
