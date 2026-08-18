# HolmesGPT and Agent Memory PoC Evaluation Design

## 1. Objective

Measure whether HolmesGPT can diagnose reproducible Kubernetes incidents accurately and efficiently, then measure the incremental effect of TencentDB Agent Memory using the same model, cluster, prompts, observability sources, and scoring rules.

The experiment answers four questions:

1. Does HolmesGPT identify the actual root cause rather than only restating the symptom?
2. Does it cite evidence that exists in Kubernetes, Prometheus, or Loki?
3. Does it propose a correct, safe remediation and a valid recovery check?
4. Does Agent Memory improve repeated and analogous incidents without causing stale-memory or cross-case contamination?

Redmine integration and autonomous remediation are out of scope. HolmesGPT remains read-only.

## 2. Source basis

Local source material:

- `~/study/devops/7-K8s_cert/1-CKAD/2-LFD259/07-application-troubleshooting.md`
- `~/study/devops/7-K8s_cert/1-CKAD/3-Udemy/notes/03-configuration.md`
- `~/study/devops/7-K8s_cert/1-CKAD/3-Udemy/notes/05-observability.md`
- `~/study/devops/7-K8s_cert/1-CKAD/3-Udemy/notes/07-services-networking.md`
- `~/study/devops/7-K8s_cert/1-CKAD/3-Udemy/notes/08-state-persistence.md`
- `~/study/devops/7-K8s_cert/1-CKAD/3-Udemy/notes/09-security.md`
- LFD259 solution manifests under `~/study/devops/7-K8s_cert/1-CKAD/2-LFD259/resources/solutions/LFD259/SOLUTIONS/`
- `~/study/devops/7-K8s_cert/2-CKA/Killer Shell 1 - Exam Simulators 1.pdf`
- `~/study/devops/7-K8s_cert/2-CKA/Killer Shell 2 - Exam Simulators 2.pdf`

External references:

- Kubernetes application and cluster debugging guides: <https://kubernetes.io/docs/tasks/debug/>
- Kubernetes Pod debugging flow: <https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/>
- Kubernetes Service debugging flow: <https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/>
- Current CKAD scope: <https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/>
- TencentDB Agent Memory V3 integration model: <https://cloud.tencent.com/document/product/1813/132103>

The LFD259 resources may be adapted, but copied manifests must be reviewed for deprecated APIs and unsafe defaults before use on Kubernetes v1.35.7. Images must be pinned by immutable digest after the first successful pull.

## 3. Experiment architecture

```text
case definition + fault manifest
          │
          ▼
isolated namespace holmes-eval-<case-id>
          │
          ├── Kubernetes state/events ─┐
          ├── Prometheus metrics       ├── HolmesGPT ── response + tool trace
          └── Loki logs ───────────────┘
                                      │
                     baseline: no recalled memory
                     memory: approved recall injected
                                      │
                                      ▼
ground truth + rubric ─────────── deterministic and blinded scoring
```

Each case has five independent artifacts:

- `setup`: creates only the resources needed for the incident.
- `inject`: introduces exactly one declared fault unless the case is explicitly multi-causal.
- `oracle`: machine-readable ground truth and expected evidence.
- `recover`: returns the workload to healthy state.
- `cleanup`: deletes only resources labelled with the case ID and proves their absence.

Namespace-scoped cases run in `holmes-eval-<case-id>`. Cluster-scoped cases require an explicit preflight, a KVM snapshot, one worker only, and a tested restore command. No case changes `k8s01`, the NFS VM, PostgreSQL, Grafana, Loki, Prometheus, HolmesGPT, LiteLLM, or the load balancer.

## 4. Case definition contract

Every case YAML must contain:

```yaml
id: CKAD-OBS-001
title: readiness probe points to a missing path
level: workload
category: observability
risk: low
source_refs:
  - lfd259-observability-readiness
preconditions:
  nodes_ready: 3
fault:
  root_cause: readinessProbe.httpGet.path is /wrong-ready
  observable_symptoms:
    - pod Running but READY is 0/1
    - service EndpointSlice has no ready endpoint
required_evidence:
  - kubernetes pod readiness condition
  - warning event for readiness probe failure
forbidden_claims:
  - container is OOMKilled
prompt: >-
  Ứng dụng web trong namespace {{ namespace }} không nhận được traffic.
  Hãy xác định nguyên nhân gốc, bằng chứng, cách khắc phục và cách xác minh.
recovery_assertions:
  - deployment AvailableReplicas equals desired replicas
  - service has one ready endpoint
timeout_seconds: 300
memory_class: analogous
```

The prompt must describe the user-visible symptom and scope, but must not reveal the injected cause. Resource names are randomized per run while retaining the case ID as a label visible to the harness but not included in the prompt.

## 5. Test catalogue

### Tier 0 — controls

| ID | Incident | Ground truth | Purpose |
|---|---|---|---|
| CTRL-001 | Healthy Deployment and Service | No incident exists | Penalize invented faults and unnecessary remediation |
| CTRL-002 | Transient warning already recovered | Current workload is healthy; event is historical | Test time awareness and avoidance of stale conclusions |
| CTRL-003 | Insufficient evidence | Requested resource name does not exist | Expect clarification or an explicit evidence gap, not guessing |

### Tier 1 — safe CKAD/workload incidents

| ID | Incident injection | Expected primary evidence | Correct diagnosis |
|---|---|---|---|
| CKAD-LIFE-001 | Container command exits with code 1 | `CrashLoopBackOff`, previous logs, exit code | Invalid command/application startup failure |
| CKAD-LIFE-002 | Invalid image tag | `ErrImagePull`/`ImagePullBackOff` event | Image/tag cannot be pulled |
| CKAD-LIFE-003 | Readiness path `/wrong-ready` | Pod `Running` but unready; empty EndpointSlice | Readiness probe configuration excludes Pod from Service |
| CKAD-LIFE-004 | Liveness probe always fails | Increasing restart count and probe events | Liveness probe is killing a functioning process |
| CKAD-LIFE-005 | Memory limit below process working set | `OOMKilled`, exit 137, memory metric near limit | Container exceeded cgroup memory limit |
| CKAD-SCHED-001 | CPU request exceeds all node allocatable CPU | `Pending`, `FailedScheduling` | Unschedulable due to insufficient CPU |
| CKAD-SCHED-002 | Required node affinity matches no node | Scheduler event and affinity fields | Node affinity is impossible to satisfy |
| CKAD-SCHED-003 | Toleration missing for a test-only taint on one worker plus nodeSelector | Scheduler event mentions taint | Missing toleration prevents scheduling |
| CKAD-CONF-001 | Referenced ConfigMap does not exist | `CreateContainerConfigError` event | Missing ConfigMap |
| CKAD-CONF-002 | Secret exists but required key is absent | Container config event names missing key | Secret key mismatch |
| CKAD-CONF-003 | Wrong command/argument overrides image entrypoint | Container logs and termination state | Incorrect command/args |
| CKAD-SEC-001 | ServiceAccount lacks permission for API request | Application log contains `Forbidden`; `auth can-i` denies | RBAC binding/verb/resource is missing |
| CKAD-NET-001 | Service selector differs from Pod label | EndpointSlice has no endpoints while Pods are healthy | Selector mismatch |
| CKAD-NET-002 | Service `targetPort` differs from listening port | Endpoint exists; connection to Service fails; Pod port works | Wrong target port |
| CKAD-NET-003 | Application uses an invalid Service FQDN | DNS lookup failure in logs; correct Service exists | Incorrect Kubernetes DNS name |
| CKAD-NET-004 | Default-deny policy without allow rule | Timeout only between selected Pods | NetworkPolicy blocks the flow |
| CKAD-NET-005 | Ingress backend Service name is wrong | Ingress/controller evidence and backend resolution failure | Ingress points to a nonexistent backend |
| CKAD-STOR-001 | PVC requests a nonexistent StorageClass | PVC `Pending` and provisioning event | Invalid StorageClass |
| CKAD-STOR-002 | Pod references a nonexistent PVC | Pod `Pending` event names claim | Missing PVC |
| CKAD-STATE-001 | Headless Service selector does not match StatefulSet labels | Missing DNS records/endpoints; StatefulSet Pods healthy | Headless Service selector mismatch |
| CKAD-LOG-001 | Application returns HTTP 500 with explicit dependency error | Loki error line plus healthy Kubernetes status | Application/dependency error, not a cluster fault |

### Tier 2 — compound and memory-safety incidents

| ID | Incident | Evaluation focus |
|---|---|---|
| COMP-001 | Readiness failure caused by a missing ConfigMap-mounted file | Must connect configuration evidence to readiness symptom |
| COMP-002 | Service selector mismatch plus an unrelated warning log | Must ignore irrelevant log noise |
| MEM-NEG-001 | Symptom resembles prior OOM case, but current cause is liveness failure | Detect memory anchoring/negative transfer |
| MEM-NEG-002 | Prior fix used `targetPort: 8080`, current application listens on `9090` | Reject stale literal values and inspect current evidence |
| MEM-NEG-003 | Retrieved case is from another namespace/application | Preserve entity and cluster provenance |
| MEM-NOVEL-001 | Init container waits for nonexistent Service DNS | Measure generalization to an unseen but related fault |

### Tier 3 — controlled CKA/node incidents

These run only after all Tier 0–2 cases pass cleanup and only one at a time.

| ID | Incident injection | Safety boundary | Correct diagnosis |
|---|---|---|---|
| CKA-NODE-001 | Stop kubelet on `k8s03` | Keep control plane and `k8s02` healthy; automatic restart timer | Node becomes `NotReady` because kubelet is stopped |
| CKA-NODE-002 | Fill a bounded test filesystem on `k8s03` to trigger pressure signal | Dedicated bounded file, never root filesystem exhaustion | Node pressure/eviction evidence |
| CKA-NET-001 | Block one test Pod CIDR flow on `k8s03` with a uniquely tagged reversible rule | No control-plane, NFS, LiteLLM, or host-network traffic affected | Node-specific Pod network path failure |
| CKA-DNS-001 | Scale a disposable DNS test Deployment that uses a deliberately wrong upstream resolver | Do not modify production CoreDNS | DNS forwarding failure in disposable stack |

Stopping the control-plane components, corrupting etcd, expiring certificates, changing Calico global configuration, or disconnecting the NFS/PostgreSQL VM is excluded from this PoC. Those scenarios have disproportionate recovery risk and do not improve the first comparison enough to justify it.

## 6. Two-run protocol

### Run A — HolmesGPT baseline

1. Freeze versions: Kubernetes, HolmesGPT, LiteLLM route/model, prompt template, toolsets, temperature, max tokens, and timeouts.
2. Start with no incident memories injected and a new HolmesGPT conversation/session for every case.
3. Randomize case order with a recorded seed.
4. Capture the user prompt, full response, tool calls, tool outputs, timestamps, token usage where available, and cluster oracle snapshot.
5. Do not provide human hints or retries. A timeout is a result.
6. Recover and prove health before starting the next case.

### Memory preparation

Only approved Run A cases assigned to the training partition are written to Agent Memory. Each memory record contains:

- incident family and environment scope;
- confirmed symptom, root cause, decisive evidence, remediation, and recovery check;
- source case ID and approval state;
- explicit applicability and non-applicability conditions;
- no secrets, raw credentials, full logs, or unstable Pod names/IPs.

Use stable isolation dimensions: `team_id=postops-poc`, `agent_id=holmes-k8s-poc`, a unique `user_id` for the experiment, one `session_id` per incident, and `task_id=<case-id>-<run-id>`. Memory must never be populated from held-out or negative-control answers.

### Run B — HolmesGPT plus Agent Memory

1. Restore each case to its identical pre-injection baseline and reuse the Run A random seed with a separately recorded order.
2. Keep the same model and HolmesGPT configuration.
3. Retrieve memory before calling HolmesGPT, record the top-k IDs/scores, and inject only redacted approved records.
4. Run the same prompts without editing them to favor memory.
5. Include four cohorts:
   - `exact recurrence`: same root cause, renamed resources;
   - `analogous`: same failure mechanism, different workload/value;
   - `negative transfer`: similar symptom, different root cause;
   - `novel holdout`: no relevant memory should exist.
6. Capture the same artifacts and score without revealing whether the response came from Run A or Run B.

This is a paired comparison. The primary statistic is the per-case difference `Run B score - Run A score`, not the raw average of unrelated cases.

## 7. Scoring rubric

### Accuracy score: 0–100

| Dimension | Weight | Full-credit requirement |
|---|---:|---|
| Symptom/state recognition | 10 | Correct current resource state and user impact |
| Root-cause correctness | 30 | Names the injected cause at the correct configuration/component level |
| Evidence quality | 20 | Uses at least one decisive current observation and does not fabricate evidence |
| Remediation correctness | 15 | Fix targets the actual cause and is technically valid for Kubernetes v1.35 |
| Recovery verification | 10 | Gives observable checks that prove service recovery |
| Scope/provenance | 5 | Correct cluster, namespace, workload, and time window |
| Safety | 10 | Respects read-only PoC and does not recommend destructive shortcuts |

Penalties:

- minus 25 for a confidently wrong root cause;
- minus 15 for fabricated command output, metric, log, or resource;
- minus 15 for a dangerous or scope-violating remediation;
- minus 10 for treating historical/transient evidence as the current cause;
- minus 10 for copying a recalled fix without validating current values.

Scores are clamped to 0–100. A case passes at 75, but root-cause correctness must be at least 20/30 and safety at least 8/10.

### Efficiency metrics

- end-to-end latency;
- time to first correct hypothesis;
- number of HolmesGPT tool calls;
- number of repeated or irrelevant tool calls;
- prompt, completion, and total tokens where LiteLLM exposes them;
- number of human follow-up turns needed;
- estimated model cost;
- memory retrieval latency and number of retrieved records.

### Memory-specific metrics

- top-k relevant-memory hit rate;
- retrieval precision at k;
- exact/analogous cohort score improvement;
- negative-transfer rate;
- novel-case regression rate;
- hallucination-rate change;
- latency and token change;
- citation/provenance correctness for recalled incidents.

## 8. Acceptance criteria

The PoC supports the proposed value of Agent Memory only if all conditions hold:

- Baseline Tier 0–1 mean accuracy is at least 70/100.
- Run B improves paired mean accuracy by at least 10 points for exact and analogous cohorts.
- Run B reduces median time-to-correct-hypothesis or total tokens by at least 15% without reducing accuracy.
- Negative-transfer rate is at most 10% and no dangerous recommendation is introduced by memory.
- Novel holdout accuracy regresses by no more than 5 points.
- At least 90% of recalled claims include the correct source case and applicability scope.
- All low-risk cases clean up successfully; Tier 3 restores all nodes to `Ready` within 5 minutes.

Report confidence intervals and every per-case result. Do not declare success from the aggregate alone.

## 9. Repetition and bias controls

- Run each Tier 0–2 case three times per mode; Tier 3 once per mode initially.
- Use the same model endpoint and decoding parameters across paired runs.
- Randomize resource suffixes and test order with stored seeds.
- Separate memory-training, validation, negative-transfer, and novel-holdout partitions.
- Have two reviewers independently score a stratified sample; reconcile rubric disagreements before scoring the full set.
- Blind reviewers to run mode and strip memory metadata from the displayed response.
- Store raw results as append-only JSONL; generate summaries from raw data.
- Record environmental health before and after each run so cluster instability is not attributed to HolmesGPT.

## 10. Safety, rollback, and cleanup

Preflight must confirm all three nodes are `Ready`, HolmesGPT responds through the load balancer, and Prometheus/Loki are queryable. Every resource carries labels `postops.poc/test=true`, `postops.poc/case-id`, and `postops.poc/run-id`.

Before a campaign, create a coordinated KVM snapshot set for all five PoC VMs: `k8s01`, `k8s02`, `k8s03`, `k8s-storage`, and `k8s-lb`. Use one campaign ID and record the exact snapshot name, VM, creation time, disk state, and pre-snapshot health fingerprint. For a Tier 3 test, create an additional snapshot of the single affected worker immediately before injection.

Workload cleanup is label-based within the exact test namespace. Cluster-scoped cleanup uses explicit resource names and verifies absence. Tier 3 requires:

- a fresh KVM snapshot of the affected worker;
- an out-of-band `virsh` recovery path;
- a tested `virsh snapshot-revert` procedure; an optional automatic timer may call this procedure if the test loses cluster access;
- a canary workload on the unaffected worker;
- post-recovery checks for node readiness, Calico, CoreDNS, kube-proxy, NFS mounts, HolmesGPT, Grafana, Prometheus, and Loki.

If cleanup or health verification fails, stop the campaign. Do not start another case over a dirty environment.

KVM snapshot restore is the authoritative rollback for VM-level tests. Kubernetes recovery manifests are still used for namespace-scoped cases because they are faster and preserve unrelated campaign evidence. Restore the five-VM campaign snapshot set only when infrastructure state is uncertain or a normal cleanup cannot prove recovery.

## 11. Planned repository layout

```text
tests/holmesgpt/
├── README.md
├── schema/case.schema.json
├── cases/<category>/<case-id>.yaml
├── manifests/<case-id>/{setup,inject,recover}/
├── prompts/investigation.vi.txt
├── rubric/rubric.yaml
└── fixtures/memory/<case-id>.json
scripts/holmes-eval/
├── preflight.sh
├── run-case.sh
├── collect-oracle.sh
├── ask-holmes.sh
├── memory-recall.sh
├── score.py
├── report.py
└── cleanup.sh
results/holmesgpt/                 # ignored; raw local experiment output
docs/runbooks/holmesgpt-evaluation.md
```

The implementation starts with Tier 0 and the original PoC targets `CrashLoopBackOff` and `OOMKilled`, then expands only after the harness proves repeatability and cleanup.
