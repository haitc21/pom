# Run B — AIC API with approved memory

## Scope

- Fresh namespace: `holmes-eval-ckad-net-001-aic-r2`
- Same fault shape, new Pods and Service: Service selector `tier=frontend`,
  Ready Pods `tier=backend`, empty EndpointSlice.
- Approved source memory: `ckad-net-001-aic-v1`.
- Model: `mistral-3.5`.

## Requests and results

| Iteration | Request ID | Live output | Memory references | Result |
|---|---|---|---|---|
| 1 | `01900000-0000-7000-8000-000000000815` | None | None | Correctly made no conclusion and did not recall memory. |
| 2 | `01900000-0000-7000-8000-000000000816` | Service selector, Ready Pod labels, empty EndpointSlice | `ckad-net-001-aic-v1`, score `0.6765970599991836` | Correct diagnosis; memory was cited as guidance, while the conclusion cited live evidence. |

## Response evaluation

The response established the causal chain from current evidence:

`Service selector tier=frontend` → no matching `tier=backend` Ready Pods →
empty EndpointSlice → no Service backend.

It then explicitly identified the remembered case as historical guidance and
recommended confirming the workload label contract before changing either the
Service selector or the workload labels. No mutation was made.

**Score: 95/100.** The memory recall, signature filter and evidence firewall
worked as intended. Deduction: it says the historical case "matches completely"
before a declared specification confirms that `backend` is the intended label;
the response nevertheless preserves the correct conditional remediation.

## Policy fix discovered during this run

Before Run B, AIC had no signature for Service routing incidents, so a valid
memory record could not be recalled. A tested signature was added requiring
both a Service selector and `endpoints=null`; it maps to
`service_routing_failure/service_selector_mismatch` and keeps the existing
requirement for iteration greater than one and current command output.
