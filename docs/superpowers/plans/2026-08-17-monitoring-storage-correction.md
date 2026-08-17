# Monitoring storage correction (PoC)

- [ ] RED: capture current Grafana/Prometheus failures and NFS-backed claims.
- [x] GREEN: install PostgreSQL on `k8s-storage` using the VM's normal filesystem; migrate Grafana to PostgreSQL.
- [ ] GREEN: keep Prometheus single-replica for the PoC; defer TSDB storage redesign until HolmesGPT validation requires it.
- [ ] Refactor Helm values and documentation so the PoC has one Grafana replica, one Prometheus replica, and Loki on NFS.
- [ ] Review configuration, security scope, and failure behaviour.
- [ ] Verify Grafana login, Prometheus readiness, Loki readiness, and HolmesGPT diagnostics.
- [ ] Update `docs/infra/k8s.md`; preserve old NFS claims as rollback artifacts until validation completes.
- [ ] No Git commit/push in this task unless explicitly requested.

Acceptance: PostgreSQL is reachable only on the internal lab network; Grafana is Ready and uses PostgreSQL; Prometheus and Loki remain minimal single-replica PoC services; Loki may use NFS, while Grafana does not use NFS for SQLite.

Out of scope: Redmine, HA PostgreSQL, Grafana replicas, Prometheus HA, dedicated PostgreSQL disks, deleting rollback data, and Git publication.
