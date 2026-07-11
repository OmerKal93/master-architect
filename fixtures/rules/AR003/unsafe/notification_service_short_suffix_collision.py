def send_notification(notification_service, user_id, body):
    # Deliberately mimics Anthropic's real "messages.create" shape (2 dotted segments) via an
    # unrelated app-level API that happens to share the method name. AR003's allowlist includes
    # this short suffix on purpose (CODEX_HANDOFF.md requires Anthropic recognition), so this
    # fires too -- a real, accepted collision-risk trade-off, not a bug. See docs.md.
    return notification_service.messages.create(user_id=user_id, body=body)
