#!/usr/bin/env bash
# Manual integration verification without real calls / real bookings by default.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API="${APP_PUBLIC_API_URL:-http://localhost:8000}"
BUSINESS_ID="${VITE_BUSINESS_ID:-}"
AGENT_ID="${RETELL_AGENT_ID:-}"
ALLOW_LIVE_BOOKING_FLAG="${1:-}"

if [[ -f .env ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    case "$line" in
      VITE_BUSINESS_ID=*|RETELL_AGENT_ID=*|OWNER_API_TOKEN=*|APP_PUBLIC_API_URL=*)
        key="${line%%=*}"
        value="${line#*=}"
        value="${value%$'\r'}"
        export "$key=$value"
        ;;
    esac
  done < .env
  BUSINESS_ID="${VITE_BUSINESS_ID:-$BUSINESS_ID}"
  AGENT_ID="${RETELL_AGENT_ID:-$AGENT_ID}"
  API="${APP_PUBLIC_API_URL:-$API}"
  OWNER_TOKEN="${OWNER_API_TOKEN:-}"
fi

if [[ -z "$BUSINESS_ID" || -z "$AGENT_ID" ]]; then
  echo "VITE_BUSINESS_ID and RETELL_AGENT_ID must be set in .env"
  exit 1
fi

echo "== health =="
curl -sf "$API/health" >/dev/null
echo "ok"

START_ISO=$(python3 - <<'PY'
from datetime import UTC, datetime, timedelta
start = (datetime.now(UTC) + timedelta(days=14)).replace(hour=14, minute=0, second=0, microsecond=0)
print(start.isoformat())
PY
)
END_ISO=$(python3 - <<'PY'
from datetime import UTC, datetime, timedelta
start = (datetime.now(UTC) + timedelta(days=14)).replace(hour=14, minute=0, second=0, microsecond=0)
print((start + timedelta(days=2)).isoformat())
PY
)

echo "== live availability (read-only) =="
AVAIL=$(curl -sf -X POST "$API/api/integrations/calcom/availability" \
  -H 'Content-Type: application/json' \
  -H "X-Owner-Token: $OWNER_TOKEN" \
  -H "X-Business-Id: $BUSINESS_ID" \
  -d "{\"business_id\":\"$BUSINESS_ID\",\"start\":\"$START_ISO\",\"end\":\"$END_ISO\"}")
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("slots=%s mocked=%s" % (len(d.get("slots", [])), d.get("mocked")))' "$AVAIL"

echo "== simulate Retell check_availability tool =="
TOOL=$(curl -sf -X POST "$API/api/retell/tools/check_availability" \
  -H 'Content-Type: application/json' \
  -d "{\"retell_agent_id\":\"$AGENT_ID\",\"start\":\"$START_ISO\",\"end\":\"$END_ISO\",\"timezone\":\"America/Chicago\",\"max_options\":3}")
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print((d.get("spoken_summary") or "")[:120]); print("available=%s options=%s" % (d.get("available"), len(d.get("options", []))))' "$TOOL"

echo "== simulate completed-call webhook (idempotent) =="
WEBHOOK=$(python3 - <<PY
import hashlib, hmac, json, os, time, urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Load RETELL_API_KEY without printing
api_key = os.environ.get("RETELL_API_KEY", "")
if not api_key:
    for line in Path(".env").read_text().splitlines():
        if line.startswith("RETELL_API_KEY="):
            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

start = datetime.now(UTC).replace(microsecond=0)
payload = {
  "event_id": "verify-call-ended-1",
  "business_id": "$BUSINESS_ID",
  "retell_call_id": "verify-retell-call-1",
  "started_at": start.isoformat(),
  "ended_at": (start + timedelta(minutes=3)).isoformat(),
  "transcript": "Verification transcript omitted from logs.",
  "caller": {"name": "Verify Caller", "phone": "+10000000001", "email": "verify@example.com"},
  "intent": "book_appointment",
  "urgency": "normal",
  "outcome": "completed",
  "requested_service": "60 min",
}
raw = json.dumps(payload).encode()
headers = {"Content-Type": "application/json"}
# Live mode requires official Retell signature when API key present
if api_key:
    ts = str(int(time.time() * 1000))
    digest = hmac.new(api_key.encode(), raw + ts.encode(), hashlib.sha256).hexdigest()
    headers["X-Retell-Signature"] = f"v={ts},d={digest}"
req = urllib.request.Request("$API/api/webhooks/retell/call-ended", data=raw, headers=headers, method="POST")
with urllib.request.urlopen(req, timeout=20) as resp:
    body = resp.read().decode()
print(body)
PY
)
python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("status=%s duplicate=%s" % (d.get("status"), d.get("duplicate")))' "$WEBHOOK"

echo "== dashboard data =="
CALLS=$(curl -sf "$API/api/businesses/$BUSINESS_ID/calls")
APPTS=$(curl -sf "$API/api/businesses/$BUSINESS_ID/appointments")
python3 -c 'import json,sys; print("calls=%s" % len(json.loads(sys.argv[1])))' "$CALLS"
python3 -c 'import json,sys; print("appointments=%s" % len(json.loads(sys.argv[1])))' "$APPTS"

if [[ -n "${OWNER_TOKEN:-}" ]]; then
  echo "== integration status =="
  RETELL_STATUS=$(curl -sf "$API/api/integrations/retell/status" \
    -H "X-Owner-Token: $OWNER_TOKEN" -H "X-Business-Id: $BUSINESS_ID")
  CAL_STATUS=$(curl -sf "$API/api/integrations/calcom/status" \
    -H "X-Owner-Token: $OWNER_TOKEN" -H "X-Business-Id: $BUSINESS_ID")
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("retell connected=%s agent=%s last=%s" % (d.get("connected"), d.get("agent_name"), d.get("last_test_status")))' "$RETELL_STATUS"
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("calcom connected=%s event=%s last=%s" % (d.get("connected"), d.get("event_type_id"), d.get("last_test_status")))' "$CAL_STATUS"
fi

if [[ "$ALLOW_LIVE_BOOKING_FLAG" == "--allow-live-booking" ]]; then
  echo "Live booking intentionally requires ALLOW_LIVE_BOOKING=true and explicit operator action."
  echo "Refusing to auto-create a real booking from this script."
  exit 2
fi

echo
echo "Verification complete. No live booking created."
echo "Proposed webhook: ${API%/}/api/webhooks/retell"
echo "Tool URLs:"
echo "  ${API%/}/api/retell/tools/check_availability"
echo "  ${API%/}/api/retell/tools/book_appointment"
