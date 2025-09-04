# Changelog

## v0.8.21

fix(whatsapp_bot): reorder message handling to check rate limits first

Move rate limit check before message processing to prevent spam. Also ensures session state is properly updated when rate limiting occurs.