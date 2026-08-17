# Reproducible HolmesGPT PoC manifests

- [ ] RED: compare the running Helm releases and identify non-reproducible values/secrets.
- [ ] GREEN: add sanitized Helm values and Secret templates for monitoring, Loki, and HolmesGPT.
- [ ] GREEN: add a runbook with install order, prerequisites, and verification commands.
- [ ] Refactor: keep credentials out of Git and document runtime-only network routes/host aliases.
- [ ] Review: check chart versions, namespace names, resource sizing, and read-only RBAC.
- [ ] Security scan: verify no API keys/passwords/certificates are present in committed files.
- [ ] Verification: render values and compare key fields with live Helm releases.
- [ ] Live test: deploy/upgrade from the documented commands only in a disposable PoC namespace.
- [ ] Cleanup: remove temporary rendered files and credentials from the workspace.
- [ ] Runbook: update `docs/infra/k8s.md`.
- [ ] No Git commit/push unless explicitly requested.

Acceptance: a new operator can recreate the Helm releases using the committed values plus locally supplied secrets, without credentials embedded in the repository.
