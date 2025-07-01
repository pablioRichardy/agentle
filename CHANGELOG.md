# Changelog

## v0.6.0

- BREAKING: renamed methods from `GenerationProvider` base class to provide more concise and easier to read method names. The changes are:
```diff
-    def create_generation_by_prompt[T = WithoutStructuredOutput](
+    def generate_by_prompt[T = WithoutStructuredOutput](
         self,
         prompt: str | Prompt | Part | Sequence[Part],
         *,
@@ -143,7 +143,7 @@ def create_generation_by_prompt[T = WithoutStructuredOutput](
         _generation_config = self._normalize_generation_config(generation_config)
 
         return run_sync(
-            self.create_generation_by_prompt_async,
+            self.generate_by_prompt_async,
             timeout=_generation_config.timeout
             if _generation_config.timeout
             else _generation_config.timeout_s * 1000
@@ -159,7 +159,7 @@ def create_generation_by_prompt[T = WithoutStructuredOutput](
             tools=tools,
         )
 
-    async def create_generation_by_prompt_async[T = WithoutStructuredOutput](
+    async def generate_by_prompt_async[T = WithoutStructuredOutput](
         self,
         prompt: str | Prompt | Part | Sequence[Part],
         *,
@@ -173,7 +173,7 @@ async def create_generation_by_prompt_async[T = WithoutStructuredOutput](
         Create a generation from a prompt asynchronously.
 
         This method converts various prompt formats into a structured message sequence
-        and calls the create_generation_async method with the converted messages.
+        and calls the generate_async method with the converted messages.
 
         Args:
             model: The model identifier to use for generation.
@@ -216,7 +216,7 @@ async def create_generation_by_prompt_async[T = WithoutStructuredOutput](
             parts=cast(Sequence[TextPart], developer_message_parts)
         )
 
-        return await self.create_generation_async(
+        return await self.generate_async(
             model=model,
             messages=[developer_message, user_message],
             response_schema=response_schema,
@@ -224,7 +224,7 @@ async def create_generation_by_prompt_async[T = WithoutStructuredOutput](
             tools=tools,
         )
 
-    def create_generation[T = WithoutStructuredOutput](
+    def generate[T = WithoutStructuredOutput](
         self,
         *,
         model: str | ModelKind | None = None,
@@ -253,7 +253,7 @@ def create_generation[T = WithoutStructuredOutput](
         _generation_config = self._normalize_generation_config(generation_config)
 
         return run_sync(
-            self.create_generation_async,
+            self.generate_async,
             timeout=_generation_config.timeout
             if _generation_config.timeout
             else _generation_config.timeout_s * 1000
@@ -269,7 +269,7 @@ def create_generation[T = WithoutStructuredOutput](
         )
 
     @abc.abstractmethod
-    async def create_generation_async[T = WithoutStructuredOutput](
+    async def generate_async[T = WithoutStructuredOutput](
         self,
         *,
         model: str | ModelKind | None = None,
```

- feat: new `BedrockGenerationProvider` for Amazon Bedrock models. This integration uses the latest ConverseAPI.
- feat: new `OllamaGenerationProvider` for fully local model inference with Ollama.
- perf: avoiding creating `client` objects every time the `generate_async` method is called in all providers that uses clients. Now, clients are instantiated in the constructor and kept while the object is not garbage collected.
- fix: properlly getting the final `model` string object inside generation providers by mapping the `ModelKind` if provided.
