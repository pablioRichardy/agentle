# Changelog

## v0.7.23
refactor(google): improve message handling and type safety

- change text check to explicit None comparison in google_part_to_part_adapter
- add ToolExecutionResult to PartToGooglePartAdapter type union
- simplify message filtering logic in message_to_google_content_adapter
- optimize message processing in google_generation_provider

## v0.7.22
fix(typo): inserting message at the beggining of the user message

## v0.7.21
fix: appending tool execution suggestion to the last assistant message

## v0.7.20 

- Add tool execution results as proper parts in the user message
