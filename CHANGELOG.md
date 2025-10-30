# Changelog

## v0.9.26
refactor(extractor): Enhance HTML processing and base64 image removal

- Consolidate BeautifulSoup operations for more robust HTML processing
- Implement comprehensive base64 image removal strategy with detailed debugging
- Add multiple removal techniques for base64 images in img tags, anchors, and styles
- Improve error handling and type checking during HTML manipulation
- Update example code to use different LLM model and async extraction method
- Add debug print statements to track base64 image removal process
- Refactor main content extraction and tag filtering logic

## v0.9.25

- refactor(extractor): reorganize imports and add model_config attribute

- Moved the import of run_sync to a more appropriate location
- Introduced model_config attribute using ConfigDict for better configuration management

refactor(whatsapp): streamline WhatsApp bot structure and introduce v2 components

- Removed unnecessary context_manager field from WhatsAppBot class.
- Updated AudioMessage class to improve type handling in convert_long_to_str method.
- Added new v2 module with BotConfig, BatchProcessorManager, and message limit definitions for enhanced configuration and processing capabilities.
- Introduced new files for in-memory batch processing and payload handling.
- Established a new WhatsAppBot class in v2 for better organization and functionality.

