#!/usr/bin/env bash
# End-to-end demo of the running API: fetch -> store -> query.
#
#   docker compose up --build -d --wait   # start the stack first
#   ./scripts/demo.sh                     # or: BASE_URL=http://localhost:8010 ./scripts/demo.sh
#
# Needs only bash and curl. JSON is pretty-printed when python3 is available.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API="$BASE_URL/api/v1/weather"

bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
show() { printf '$ %s\n' "$*"; }

pretty() {
  local raw
  raw="$(cat)"
  if command -v python3 >/dev/null 2>&1 &&
    printf '%s' "$raw" | python3 -c 'import json, sys; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))' 2>/dev/null; then
    return
  fi
  printf '%s\n' "$raw" # not JSON, or no python3: print as-is
}

# call METHOD URL: prints the command, the HTTP status and the JSON body.
call() {
  local method="$1" url="$2" body status
  show "curl -X $method \"$url\""
  body="$(curl -sS -X "$method" -w '\n%{http_code}' "$url")"
  status="${body##*$'\n'}"
  body="${body%$'\n'*}"
  echo "HTTP $status"
  printf '%s' "$body" | pretty
}

# Print one numeric field of a compact JSON response, e.g. `field id` (no python3 needed).
field() {
  sed -n "s/.*\"$1\":\([0-9][0-9]*\).*/\1/p" | head -n 1
}

bold "0. Is the stack up?"
for _ in $(seq 1 30); do
  curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && break
  sleep 2
done
call GET "$BASE_URL/health"

bold "1. Fetch the current weather from OpenWeather and store it (dynamic city/units/lang)"
call POST "$API/fetch?city=Florianopolis,BR&units=metric&lang=pt_br"
call POST "$API/fetch?city=Sao%20Paulo,BR&units=imperial&lang=en"

bold "2. Idempotency: fetching the same observation again updates the same row"
first_id="$(curl -sS -X POST "$API/fetch?city=Curitiba,BR" | field id)"
again_id="$(curl -sS -X POST "$API/fetch?city=Curitiba,BR" | field id)"
echo "Curitiba fetched twice -> ids $first_id and $again_id"

bold "3. Query the stored data (filters + pagination; city match ignores case and accents)"
call GET "$API?city=florian%C3%B3polis&limit=5" # "florianópolis", URL-encoded
call GET "$API?limit=10&offset=0"

bold "4. Latest reading for a city, and one reading by id"
call GET "$API/latest?city=Sao%20Paulo"
call GET "$API/$first_id"

bold "5. Errors are explicit"
call POST "$API/fetch?city=Atlantis-Does-Not-Exist"
call GET "$API?limit=500"

bold "Done. Explore the rest in Swagger UI: $BASE_URL/docs"
