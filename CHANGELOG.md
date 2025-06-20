# Changelog

## v0.5.0

- feat(experimental): integration with `EvolutionAPI`.
- feat: new `compile_if` method to the `Prompt` class to provide an easy way to only compile valid keys in a prompt.
- feat: new kind of part: `ToolExecutionResult` in the parts of `UserMessage` and `AssistantMessage`'s.
- feat: utility methods to `AgentRunOutput` and `Generation` classes.
- fix: wrong boolean comparison when trying to get the message from a choice in a generation.
- fix: `DeveloperMessage` not beeing properlly propagated in some cases in `Agent` class.
- fix: tool calls not beeing properlly awaited.
