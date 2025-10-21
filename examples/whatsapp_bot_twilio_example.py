# examples/whatsapp_bot_twilio_example.py
"""
Example of using Agentle agents as WhatsApp bots with Twilio API provider.
"""

import asyncio
import logging
import os

import uvicorn
from blacksheep import Application
from dotenv import load_dotenv

from agentle.agents.agent import Agent
from agentle.agents.conversations.json_file_conversation_store import (
    JSONFileConversationStore,
)
from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig
from agentle.agents.whatsapp.models.whatsapp_session import WhatsAppSession
from agentle.agents.whatsapp.providers.twilio.twilio_api_config import (
    TwilioAPIConfig,
)
from agentle.agents.whatsapp.providers.twilio.twilio_api_provider import (
    TwilioAPIProvider,
)
from agentle.agents.whatsapp.whatsapp_bot import WhatsAppBot
from agentle.sessions.in_memory_session_store import InMemorySessionStore
from agentle.sessions.session_manager import SessionManager

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)


def create_bot() -> Application:
    """Example: Production bot with Twilio API provider and optimized configuration."""

    agent = Agent(
        instructions="Você é um assistente profissional. Seja útil, cortês e eficiente. Responda todas as perguntas.",
        conversation_store=JSONFileConversationStore(),
    )

    session_manager = SessionManager[WhatsAppSession](
        session_store=InMemorySessionStore[WhatsAppSession](),
        default_ttl_seconds=3600,
        enable_events=True,
    )

    # Create Twilio provider with session management
    provider = TwilioAPIProvider(
        config=TwilioAPIConfig(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", "your-account-sid"),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", "your-auth-token"),
            whatsapp_number=os.getenv(
                "TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"
            ),
            webhook_url=os.getenv(
                "TWILIO_WEBHOOK_URL",
                "https://wrongly-delicate-trout.ngrok-free.app/webhook/whatsapp",
            ),
            timeout=int(os.getenv("TWILIO_TIMEOUT", "30")),
            status_callback_url=os.getenv("TWILIO_STATUS_CALLBACK_URL"),
        ),
        session_manager=session_manager,
        session_ttl_seconds=3600,
        enable_circuit_breaker=True,
        enable_rate_limiting=True,
        max_retries=3,
        base_retry_delay=1.0,
        connection_pool_size=100,
    )

    # Use production configuration preset
    bot_config = WhatsAppBotConfig.production(
        welcome_message="Mensagem inicial.",
        quote_messages=False,  # Don't quote by default
        enable_spam_protection=True,
    )

    # Validate configuration
    issues = bot_config.validate_config()
    if issues:
        logging.warning(f"Production configuration issues: {issues}")

    whatsapp_bot = WhatsAppBot(agent=agent, provider=provider, config=bot_config)
    whatsapp_bot.start()

    # Optional: Send a test message to verify the setup
    # Uncomment the lines below to send a test message
    async def send_test_message():
        await whatsapp_bot.send_message(
            to="+1234567890",  # Replace with actual phone number
            message="Teste de configuração do bot Twilio",
        )

    asyncio.run(send_test_message())

    return whatsapp_bot.to_blacksheep_app(
        webhook_path="/webhook/whatsapp",
        show_error_details=False,
    )


app = create_bot()
port = int(os.getenv("PORT", "8000"))

if __name__ == "__main__":
    # Log which bot type is being used
    bot_type = os.getenv("BOT_TYPE", "twilio")
    logging.info(
        f"Starting WhatsApp bot server with Twilio API provider on port {port}"
    )

    uvicorn.run(app, host="0.0.0.0", port=port)
