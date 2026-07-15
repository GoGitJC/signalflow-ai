#!/usr/bin/env bash
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"
BUSINESS_ID="${BUSINESS_ID:?Set BUSINESS_ID to a business UUID}"
START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
END="$(date -u -d '+4 minutes' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+4M +%Y-%m-%dT%H:%M:%SZ)"
TOMORROW="$(date -u -d '+1 day' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+1d +%Y-%m-%dT%H:%M:%SZ)"
TOMORROW_END="$(date -u -d '+1 day 30 minutes' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+1d -v+30M +%Y-%m-%dT%H:%M:%SZ)"
curl -sS -X POST "$API_URL/api/webhooks/retell/call-ended" -H 'Content-Type: application/json' -d "{
  \"event_id\": \"demo-$(date +%s)\", \"business_id\": \"$BUSINESS_ID\", \"retell_call_id\": \"demo-call-$(date +%s)\",
  \"started_at\": \"$START\", \"ended_at\": \"$END\", \"transcript\": \"I need an AC repair tomorrow. The unit is not cooling.\",
  \"caller\": {\"name\": \"Jordan Lee\", \"phone\": \"+12105550199\", \"email\": \"jordan@example.com\"},
  \"intent\": \"book_appointment\", \"urgency\": \"urgent\", \"outcome\": \"appointment_booked\", \"requested_service\": \"AC repair\",
  \"appointment\": {\"cal_event_id\": \"demo-cal-$(date +%s)\", \"service\": \"AC repair\", \"start_time\": \"$TOMORROW\", \"end_time\": \"$TOMORROW_END\", \"status\": \"booked\"}
}" | python -m json.tool
