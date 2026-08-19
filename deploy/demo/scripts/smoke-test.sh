#!/usr/bin/env bash
set -euo pipefail

base_url="${AIC_BASE_URL:-http://127.0.0.1:8080}"
first=$(curl --fail --silent --header 'Content-Type: application/json' \
  --data '{"request_id":"01900000-0000-7000-8000-000000000001","conversation_id":null,"model":"mistral-3.5","message":"Pod checkout-api is CrashLoopBackOff in namespace demo. Investigate read-only and report evidence.","context":{"cluster":"k8s-poc","namespace":"demo"},"command_outputs":[]}' \
  "$base_url/api/chat")
conversation_id=$(printf '%s' "$first" | python3 -c 'import json,sys; print(json.load(sys.stdin)["conversation_id"])')

second=$(curl --fail --silent --header 'Content-Type: application/json' \
  --data "{\"request_id\":\"01900000-0000-7000-8000-000000000002\",\"conversation_id\":\"$conversation_id\",\"model\":\"mistral-3.5\",\"message\":\"The engineer ran the suggested read-only check and provides its output. Reassess the hypothesis.\",\"context\":{\"cluster\":\"k8s-poc\",\"namespace\":\"demo\"},\"command_outputs\":[{\"command\":\"kubectl -n demo describe pod checkout-api-abc\",\"exit_code\":0,\"output\":\"Last State: Terminated; Reason: OOMKilled; Exit Code: 137\"}]}" \
  "$base_url/api/chat")

printf '%s\n' "$first" "$second" | python3 -c 'import json,sys; rows=[json.loads(x) for x in sys.stdin if x.strip()]; assert rows[0]["iteration"] == 1; assert rows[1]["iteration"] == 2; print(json.dumps({"ok":True,"conversation_id":rows[0]["conversation_id"],"iterations":[r["iteration"] for r in rows],"memory_references":len(rows[0].get("memory_references",[]))},ensure_ascii=False))'
