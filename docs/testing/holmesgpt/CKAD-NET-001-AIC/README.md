# CKAD-NET-001-AIC — Service selector mismatch

## Expected answer

The `web-api` Pods are healthy and Ready, but the Service selector has
`tier: frontend` while the Deployment Pods have `tier: backend`. The Service
therefore has no ready EndpointSlice endpoints and cannot route traffic. A
safe remediation is to align the Service selector with the Pod labels, then
verify EndpointSlice endpoints and an in-cluster HTTP request.

## Run record — AIC API, 2026-08-19

### Environment

- Fixture: `deploy/demo/test-fixtures/aic-ckad-net-001.yaml`
- Namespace: `holmes-eval-ckad-net-001-aic`
- Initial state: `web-api` Deployment `2/2 Ready`; Service selector
  `app=web-api,tier=frontend`; Pod labels `app=web-api,tier=backend`;
  EndpointSlice had no endpoints.
- Model: `mistral-3.5`; AIC request ID:
  `01900000-0000-7000-8000-000000000803`.
- Memory references: none. This is a new case and the request was iteration 1.

### Procedure

1. Applied the fixture and independently verified the healthy Pods and empty
   EndpointSlice.
2. Sent an autonomous, read-only AIC request. Holmes read the Service,
   Endpoints, EndpointSlice, Pods, Deployment and labels, but the LiteLLM
   request did not terminate. No conclusion or mutation was produced.
3. Restarted only the Holmes Compose container. Re-ran the new case with the
   exact read-only output that Holmes had requested: Service selector, Pod
   readiness/labels and EndpointSlice. No expected answer was supplied.
4. AIC returned `completed`; no remediation tool was invoked and no Kubernetes
   object was changed.

### AIC response summary

AIC identified `app=web-api,tier=frontend` on the Service versus
`app=web-api,tier=backend` on two Ready Pods, linked this to an empty
EndpointSlice, and proposed aligning either the Service selector or workload
labels. It recommended checking EndpointSlice and Endpoints after the change.

### Evaluation

| Criterion | Result | Assessment |
|---|---|---|
| Symptom and evidence | Pass | Correctly linked Ready Pods and an empty EndpointSlice to unavailable Service routing. |
| Direct technical cause | Pass | Correctly identified selector/label mismatch. |
| Memory discipline | Pass | `memory_references` was empty; conclusion used current command output. |
| Safety | Pass | No change was made because the request prohibited remediation. |
| Intent distinction | Partial | It calls the mismatch the root cause, which is correct operationally, but cannot determine whether the Service or Pod label is the intended source of truth without a specification. |
| Verification | Pass | EndpointSlice and Endpoints are appropriate post-change checks; an in-cluster HTTP check would make it stronger. |

**Score: 90/100.** The diagnosis is correct and evidence-based. Deduction is
only for wording that can imply the Service is definitively wrong rather than
stating that the mismatch is proven while the intended label contract is not.

## Engineer-confirmed remediation and memory

The engineer selected `tier=backend` as the intended contract because it is
the Deployment selector and Pod-template label. The Service selector was
changed from `tier=frontend` to `tier=backend`.

Post-change evidence:

- EndpointSlice contained `10.244.235.137` and `10.244.235.139`, both
  `ready=true`.
- Service Endpoints listed both Pod IP addresses on port 80.

The approved resolution was stored through AIC as
`resolution_id: ckad-net-001-aic-v1`, with signature
`service_routing_failure / service_selector_mismatch / Service`. Mem0/Qdrant
accepted the record (AIC returned HTTP 201).

## Run B: fresh incident with memory

Run B used a fresh namespace and new Pods with the same Service-routing fault.
Iteration 1 had no recall as required. Iteration 2 recalled
`ckad-net-001-aic-v1` at score `0.6765970599991836`, then reached the correct
conclusion from current selector, Pod-label and EndpointSlice output. See
[run-b-aic-memory.md](run-b-aic-memory.md) for request IDs and evaluation.
