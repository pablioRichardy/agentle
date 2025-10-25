"""
Example: WhatsApp Bot with Text-to-Speech (TTS) Integration

This example demonstrates how to configure a WhatsApp bot to send audio responses
using a TTS provider instead of text messages.
"""

import asyncio

from agentle.agents.agent import Agent
from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig
from agentle.agents.whatsapp.providers.evolution.evolution_api_config import (
    EvolutionAPIConfig,
)
from agentle.agents.whatsapp.providers.evolution.evolution_api_provider import (
    EvolutionAPIProvider,
)
from agentle.agents.whatsapp.whatsapp_bot import WhatsAppBot
from agentle.tts.speech_config import SpeechConfig

# Import your TTS provider (example with ElevenLabs)
# from agentle.tts.elevenlabs_tts_provider import ElevenLabsTtsProvider


async def main():
    # 1. Configure your agent
    agent = Agent(
        name="TTS Assistant",
        instructions="You are a helpful voice assistant. Keep responses concise and natural for speech.",
        # ... other agent configuration
    )

    # 2. Configure Evolution API provider
    evolution_config = EvolutionAPIConfig(
        base_url="https://your-evolution-api.com",
        instance_name="your-instance",
        api_key="your-api-key",
    )
    provider = EvolutionAPIProvider(config=evolution_config)

    # 3. Configure TTS provider (example with ElevenLabs)
    # Replace with your actual TTS provider
    # tts_provider = ElevenLabsTtsProvider(api_key="your-elevenlabs-api-key")

    # 4. Configure speech settings
    speech_config = SpeechConfig(
        voice_id="your-voice-id",  # e.g., ElevenLabs voice ID
        model_id="eleven_multilingual_v2",  # Optional: specific model
        output_format="mp3_22050_32",  # Audio format
        language_code="en-US",  # Optional: language code
    )

    # 5. Configure WhatsApp bot with TTS
    bot_config = WhatsAppBotConfig.production(
        welcome_message="Hello! I'm your voice assistant.",
        quote_messages=True,
    ).with_overrides(
        # TTS Configuration
        speech_play_chance=1.0,  # 100% chance to send audio (set to 0.5 for 50%, etc.)
        speech_config=speech_config,
        # Other settings
        typing_indicator=True,
        typing_duration=2,
    )

    # 6. Create WhatsApp bot with TTS
    bot = WhatsAppBot(
        agent=agent,
        provider=provider,
        # tts_provider=tts_provider,  # Uncomment when you have a TTS provider
        config=bot_config,
    )

    # 7. Start the bot
    await bot.start_async()

    print("WhatsApp bot with TTS is running!")
    print(f"Speech play chance: {bot_config.speech_play_chance * 100}%")
    print(f"Voice ID: {speech_config.voice_id}")

    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        await bot.stop_async()


if __name__ == "__main__":
    asyncio.run(main())
