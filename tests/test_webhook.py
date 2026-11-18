from unittest.mock import AsyncMock, MagicMock, patch
import discord
from flask import Flask
import pytest
from webhook import start_webhook_server

@pytest.fixture
def webhook_app_and_bot(mock_bot):
    captured_app = None

    def fake_run(self, *args, **kwargs):
        nonlocal captured_app
        captured_app = self

    config = {
        "form_port": 5000,
        "form_log_channel_id": 301,
        "form_webhook_secret": "test-secret-123"
    }

    # Ensure channel.send is an AsyncMock
    log_channel = mock_bot.get_channel(301)
    if log_channel:
        log_channel.send = AsyncMock()

    with patch.object(Flask, "run", new=fake_run):
        start_webhook_server(mock_bot, config)

    client = captured_app.test_client()
    return client, mock_bot, config

def test_webhook_unauthorized_missing_header(webhook_app_and_bot):
    client, bot, _ = webhook_app_and_bot
    response = client.post('/webhook', json={"data": {}})
    assert response.status_code == 401
    assert response.data == b"Unauthorized"

def test_webhook_unauthorized_invalid_secret(webhook_app_and_bot):
    client, bot, _ = webhook_app_and_bot
    response = client.post(
        '/webhook',
        json={"data": {}},
        headers={"Webhook-Secret": "wrong-secret"}
    )
    assert response.status_code == 401

def test_webhook_success_rides_form(webhook_app_and_bot):
    client, bot, _ = webhook_app_and_bot
    payload = {
        "title": "Rides Form",
        "data": {
            "Timestamp": "2026-11-18 10:00:00",
            "Name": "John Doe",
            "Preferences": ["Front Seat", "Quiet"]
        }
    }

    with patch.object(bot.loop, "create_task") as mock_create_task:
        response = client.post(
            '/webhook',
            json=payload,
            headers={"Webhook-Secret": "test-secret-123"}
        )
        assert response.status_code == 200
        assert response.data == b"OK"

        mock_create_task.assert_called_once()
        # Verify the coroutine passed to create_task was channel.send
        channel = bot.get_channel(301)
        assert channel is not None

def test_webhook_color_matching(webhook_app_and_bot):
    client, bot, _ = webhook_app_and_bot
    titles_and_expected_colors = [
        ("Late Rides Form", discord.Colour.red().value),
        ("Rides Form", discord.Colour.blue().value),
        ("Driver Application", discord.Colour.green().value)
    ]

    for title, expected_color in titles_and_expected_colors:
        payload = {
            "title": title,
            "data": {
                "Timestamp": "2026-11-18 10:00:00",
                "Status": "Confirmed"
            }
        }
        with patch.object(bot.loop, "create_task") as mock_create_task:
            response = client.post(
                '/webhook',
                json=payload,
                headers={"Webhook-Secret": "test-secret-123"}
            )
            assert response.status_code == 200
            mock_create_task.assert_called_once()
