from pathlib import Path


target = Path("/app/kubernetes_remediation.py")
source = target.read_text()
old = "def run_kubectl_command(args: List[str]) -> Dict[str, Any]:"
new = (
    "def run_kubectl_command(\n"
    "    args: List[str], __robusta_user_approved: bool = False\n"
    ") -> Dict[str, Any]:"
)
if old not in source:
    raise SystemExit("upstream run_kubectl_command signature not found")
target.write_text(source.replace(old, new, 1))
