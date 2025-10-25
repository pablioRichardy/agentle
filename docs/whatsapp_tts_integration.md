# WhatsApp Text-to-Speech (TTS) Integration

This document explains how to integrate Text-to-Speech (TTS) functionality with your WhatsApp bot, allowing it to send audio responses instead of text messages.

## Overview

The WhatsApp bot now supports sending audio responses using any TTS provider that implements the `TtsProvider` interface. When configured, the bot can:

- Convert text responses to speech
- Send audio messages to WhatsApp users
- Automatically fall back to text if TTS fails
- Control the probability of sending audio vs text

## Architecture

### Components

1. **TtsProvider**: Abstract interface for TTS providers
2. **WhatsAppProvider.send_audio_message()**: New method for sending audio messages
3. **WhatsAppBotConfig**: Configuration for TTS behavior
4. **WhatsAppBot**: Integration logic that orchestrates TTS and message sending

### Flow

```
User Message → Agent Processing → Text Response
                                        ↓
                            [TTS Enabled & Random Check]
                                        ↓
                            ┌───────────┴───────────┐
                            ↓                       ↓
                    TTS Synthesis              Skip TTS
                            ↓                       ↓
                    Audio Message           Text Message
                            ↓                       ↓
                    send_audio_message()    send_text_message()
```

## Configuration

### 1. Speech Configuration

Create a `SpeechConfig` with your TTS provider settings:

```python
from agentle.tts.speech_config import SpeechConfig

speech_config = SpeechConfig(
    voice_id="your-voice-id",           # Required: Voice identifier
    model_id="model-name",              # Optional: TTS model
    output_format="mp3_22050_32",       # Audio format
    language_code="en-US",              # Optional: Language
    voice_settings=VoiceSettings(...)   # Optional: Voice customization
)
```

### 2. Bot Configuration

Configure the WhatsApp bot with TTS settings:

```python
from agentle.agents.whatsapp.models.whatsapp_bot_config import WhatsAppBotConfig

config = WhatsAppBotConfig(
    # TTS Settings
    speech_play_chance=0.8,      # 80% chance to send audio
    speech_config=speech_config,  # Your speech configuration
    
    # Other settings...
    typing_indicator=True,
    quote_messages=True,
)
```

### 3. Bot Initialization

Create the bot with a TTS provider:

```python
from agentle.agents.whatsapp.whatsapp_bot import WhatsAppBot

bot = WhatsAppBot(
    agent=your_agent,
    provider=whatsapp_provider,
    tts_provider=your_tts_provider,  # Implement TtsProvider interface
    config=config,
)
```

## Configuration Options

### `speech_play_chance`

- **Type**: `float` (0.0 to 1.0)
- **Default**: `0.0` (disabled)
- **Description**: Probability of sending audio instead of text
- **Examples**:
  - `0.0`: Never send audio (TTS disabled)
  - `0.5`: 50% chance of audio
  - `1.0`: Always send audio

### `speech_config`

- **Type**: `SpeechConfig | None`
- **Default**: `None`
- **Description**: Configuration for TTS synthesis
- **Required**: Must be set if `speech_play_chance > 0`

## Implementation Details

### New Provider Method

The `WhatsAppProvider` base class now includes:

```python
async def send_audio_message(
    self,
    to: str,
    audio_base64: str,
    quoted_message_id: str | None = None,
) -> WhatsAppMediaMessage:
    """
    Send an audio message (optimized for voice/TTS).
    
    Args:
        to: Recipient phone number
        audio_base64: Base64-encoded audio data
        quoted_message_id: Optional message to quote
        
    Returns:
        The sent audio message
    """
```

### Evolution API Implementation

The `EvolutionAPIProvider` implements this using the `/sendWhatsAppAudio` endpoint:

```python
# Payload structure
{
    "number": "5511999999999@s.whatsapp.net",
    "audio": "base64_encoded_audio_data",
    "quoted": {  # Optional
        "key": {"id": "message_id"}
    }
}
```

## Error Handling

The TTS integration includes robust error handling:

1. **TTS Synthesis Failure**: Falls back to text message
2. **Audio Send Failure**: Falls back to text message
3. **Missing Configuration**: Skips TTS if `speech_config` is not set
4. **Network Issues**: Retries with exponential backoff (via provider)

All errors are logged with context for debugging.

## Usage Examples

### Example 1: Always Send Audio

```python
config = WhatsAppBotConfig(
    speech_play_chance=1.0,  # 100% audio
    speech_config=SpeechConfig(
        voice_id="voice-123",
        output_format="mp3_22050_32",
    ),
)
```

### Example 2: 50/50 Mix

```python
config = WhatsAppBotConfig(
    speech_play_chance=0.5,  # 50% audio, 50% text
    speech_config=SpeechConfig(
        voice_id="voice-123",
        language_code="pt-BR",
    ),
)
```

### Example 3: Text Only (Default)

```python
config = WhatsAppBotConfig(
    speech_play_chance=0.0,  # No audio
    # speech_config not needed
)
```

### Example 4: Using with Presets

```python
config = WhatsAppBotConfig.customer_service(
    welcome_message="Hello! How can I help you?",
).with_overrides(
    speech_play_chance=0.3,  # 30% audio responses
    speech_config=SpeechConfig(
        voice_id="professional-voice",
        model_id="eleven_multilingual_v2",
    ),
)
```

## Best Practices

### 1. Voice Selection

Choose voices appropriate for your use case:
- **Customer Service**: Professional, clear voices
- **Casual Chat**: Friendly, conversational voices
- **Multilingual**: Use voices that support your target languages

### 2. Audio Format

Recommended formats for WhatsApp:
- `mp3_22050_32`: Good balance of quality and size
- `mp3_44100_128`: Higher quality for important messages
- `opus`: Efficient compression for mobile networks

### 3. Response Length

Keep TTS responses concise:
- Long audio messages can be tedious
- Consider splitting long responses into text
- Use `speech_play_chance < 1.0` for variety

### 4. Fallback Strategy

Always configure proper fallback:
```python
# The bot automatically falls back to text on TTS failure
# No additional configuration needed
```

### 5. Testing

Test with different scenarios:
```python
# Test with different chances
for chance in [0.0, 0.5, 1.0]:
    config = config.with_overrides(speech_play_chance=chance)
    # Test bot behavior
```

## Monitoring

The bot logs TTS activity:

```
[TTS] Attempting to send audio response to 5511999999999 (chance: 80.0%)
[TTS] Successfully sent audio response to 5511999999999
```

Or on failure:
```
[TTS] Failed to send audio response to 5511999999999, falling back to text: <error>
```

## Performance Considerations

### Latency

TTS adds latency to responses:
- Synthesis time: 1-3 seconds (varies by provider)
- Upload time: 0.5-2 seconds (depends on audio size)
- Total overhead: ~2-5 seconds

Consider using `typing_indicator` to manage user expectations:
```python
config = WhatsAppBotConfig(
    typing_indicator=True,
    typing_duration=3,  # Show typing while synthesizing
    speech_play_chance=1.0,
)
```

### Costs

TTS providers typically charge per character:
- Monitor usage with `speech_play_chance < 1.0`
- Use shorter responses for audio
- Consider text for long explanations

### Bandwidth

Audio messages are larger than text:
- MP3 (22kHz): ~2KB per second of audio
- Consider user's network conditions
- Use efficient formats like Opus

## Troubleshooting

### Audio Not Sending

Check:
1. `speech_play_chance > 0`
2. `speech_config` is set
3. `tts_provider` is provided to bot
4. TTS provider credentials are valid

### Always Falling Back to Text

Check logs for:
- TTS synthesis errors
- Audio upload failures
- Provider configuration issues

### Audio Quality Issues

Adjust `SpeechConfig`:
```python
speech_config = SpeechConfig(
    voice_id="high-quality-voice",
    output_format="mp3_44100_128",  # Higher quality
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
    ),
)
```

## Future Enhancements

Potential improvements:
- [ ] Caching synthesized audio for repeated responses
- [ ] Adaptive quality based on network conditions
- [ ] Voice selection based on user preferences
- [ ] Streaming audio for long responses
- [ ] Multi-language voice switching

## API Reference

See:
- `agentle.tts.tts_provider.TtsProvider`
- `agentle.tts.speech_config.SpeechConfig`
- `agentle.agents.whatsapp.providers.base.whatsapp_provider.WhatsAppProvider.send_audio_message()`
- `agentle.agents.whatsapp.models.whatsapp_bot_config.WhatsAppBotConfig`
