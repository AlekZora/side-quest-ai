extends Node2D

## Step 7 milestone: walk a placeholder player into the NPC's talk zone, press
## E, and pull a generated quest out of the Python bridge over HTTP.
## Placeholder visuals only — coloured rectangles, no art.

const HEALTH_URL := "http://localhost:8000/health"
const QUEST_URL := "http://localhost:8000/generate-quest"
const PLAYER_ACTION := "Bribed the eastern gate guard to pass through after curfew"

const SPEED := 220.0
const PROMPT_TEXT := "Press E to talk"
const WAITING_TEXT := "..."

@onready var health_request: HTTPRequest = $HTTPRequest
@onready var quest_request: HTTPRequest = $QuestRequest
@onready var player: Area2D = $Player
@onready var talk_zone: Area2D = $NPC/TalkZone
@onready var dialogue: RichTextLabel = $UI/DialoguePanel/MarginContainer/DialogueLabel

var _player_in_range := false
var _request_in_flight := false


func _ready() -> void:
	dialogue.text = ""

	talk_zone.area_entered.connect(_on_talk_zone_area_entered)
	talk_zone.area_exited.connect(_on_talk_zone_area_exited)

	health_request.request_completed.connect(_on_health_completed)
	quest_request.request_completed.connect(_on_quest_completed)

	# A real generation round trip runs ~20-40s (Haiku call, plus a retry when
	# validation fails). Without this the request would hang forever instead.
	quest_request.timeout = 120.0

	print("[bridge] GET %s" % HEALTH_URL)

	# request() returning anything but OK means the request was never sent —
	# bad URL, no free connection, HTTPRequest still busy.
	var err: int = health_request.request(HEALTH_URL)
	if err != OK:
		printerr("[bridge] ERROR — request was not sent. error %d (%s)" % [err, error_string(err)])
		push_error("[bridge] could not send request to %s" % HEALTH_URL)


func _process(delta: float) -> void:
	var direction := Vector2(
		Input.get_axis("ui_left", "ui_right"),
		Input.get_axis("ui_up", "ui_down")
	)
	if direction != Vector2.ZERO:
		player.position += direction.normalized() * SPEED * delta


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_E:
		_request_quest()


# ── Proximity ─────────────────────────────────────────────────────────────────

func _on_talk_zone_area_entered(area: Area2D) -> void:
	if area != player:
		return
	_player_in_range = true
	print("[bridge] player entered talk zone")
	if not _request_in_flight:
		dialogue.text = PROMPT_TEXT


func _on_talk_zone_area_exited(area: Area2D) -> void:
	if area != player:
		return
	_player_in_range = false
	print("[bridge] player left talk zone")
	if not _request_in_flight:
		dialogue.text = ""


# ── Quest request ─────────────────────────────────────────────────────────────

func _request_quest() -> void:
	if not _player_in_range:
		return
	if _request_in_flight:
		print("[bridge] request already in flight — ignoring E")
		return

	_request_in_flight = true
	dialogue.text = WAITING_TEXT

	var payload := JSON.stringify({"player_action": PLAYER_ACTION})
	var headers := PackedStringArray(["Content-Type: application/json"])

	print("[bridge] POST %s" % QUEST_URL)

	var err: int = quest_request.request(QUEST_URL, headers, HTTPClient.METHOD_POST, payload)
	if err != OK:
		_request_in_flight = false
		var send_error := "request was not sent — error %d (%s)" % [err, error_string(err)]
		printerr("[bridge] ERROR — %s" % send_error)
		push_error("[bridge] %s" % send_error)
		_show_error(send_error)


func _on_quest_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	_request_in_flight = false

	# Sent but never came back — server down, timeout, connection refused.
	if result != HTTPRequest.RESULT_SUCCESS:
		var net_error := "request did not complete (result %d). Is the server running?" % result
		printerr("[bridge] ERROR — %s" % net_error)
		push_error("[bridge] %s" % net_error)
		_show_error(net_error)
		return

	print("[bridge] HTTP status code: %d" % response_code)

	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		var parse_error := "could not parse response as JSON (HTTP %d)" % response_code
		printerr("[bridge] ERROR — %s" % parse_error)
		_show_error(parse_error)
		return

	var data: Variant = json.data
	if typeof(data) != TYPE_DICTIONARY:
		var shape_error := "unexpected response shape (HTTP %d)" % response_code
		printerr("[bridge] ERROR — %s" % shape_error)
		_show_error(shape_error)
		return

	# The server answers 200 with ok=false for pipeline failures, so the status
	# code alone is not enough to know the request succeeded.
	if not data.get("ok", false):
		var server_error := str(data.get("error", "server reported ok=false"))
		printerr("[bridge] ERROR — server said: %s" % server_error)
		_show_error(server_error)
		return

	# JSON numbers parse as float, so attempts arrives as 2.0 without this.
	var attempts_value: Variant = data.get("attempts", null)
	var attempts_text := "?" if attempts_value == null else str(int(attempts_value))

	print("[bridge] npc=%s template=%s validation=%s attempts=%s" % [
		data.get("npc_name", "?"),
		data.get("template", "?"),
		data.get("validation_status", "?"),
		attempts_text,
	])

	_print_attempt_log(data.get("attempt_log", null))

	var quest_text := str(data.get("quest_text", ""))
	if quest_text.is_empty():
		_show_error("server returned ok=true but no quest_text")
		return

	dialogue.text = quest_text


# ── Health check (unchanged from the first bridge test) ───────────────────────

func _on_health_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	# The request was sent but did not complete — server down, DNS, TLS, timeout.
	if result != HTTPRequest.RESULT_SUCCESS:
		printerr("[bridge] ERROR — request did not complete. result %d" % result)
		printerr("[bridge] is the server running?  uvicorn server:app --port 8000")
		push_error("[bridge] request to %s failed with result %d" % [HEALTH_URL, result])
		return

	print("[bridge] HTTP status code: %d" % response_code)
	print("[bridge] response body: %s" % body.get_string_from_utf8())


func _print_attempt_log(attempt_log: Variant) -> void:
	# One line per draft: which checks failed, whether it retried, and why.
	# Older builds of the server do not send attempt_log, so absence is fine.
	if not (attempt_log is Array):
		return

	for entry in attempt_log:
		if typeof(entry) != TYPE_DICTIONARY:
			continue

		var failed_text := "none"
		var failed: Variant = entry.get("failed", [])
		if failed is Array and not failed.is_empty():
			var parts := PackedStringArray()
			for check in failed:
				parts.append(str(check))
			failed_text = ", ".join(parts)

		print("[bridge]   attempt %s: failed=%s retried=%s — %s" % [
			str(int(entry.get("attempt", 0))),
			failed_text,
			str(entry.get("retried", false)),
			str(entry.get("reason", "")),
		])


func _show_error(message: String) -> void:
	dialogue.text = "ERROR: %s" % message
