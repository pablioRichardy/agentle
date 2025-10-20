from collections.abc import Sequence
from textwrap import dedent

from html_to_markdown import convert
from rsb.models import Field
from rsb.models.base_model import BaseModel

from agentle.prompts.models.prompt import Prompt
from agentle.responses.definitions.reasoning import Reasoning
from agentle.responses.responder import Responder
from agentle.utils.needs import needs
from agentle.web.actions.action import Action
from agentle.web.extraction_preferences import ExtractionPreferences
from agentle.web.extraction_result import ExtractionResult

_INSTRUCTIONS = Prompt.from_text(
    dedent("""\
    <character>You are a specialist in data extraction and web content analysis. Your role is to act as an intelligent and precise data processor.</character>
    
    <request>Your task is to analyze the content of a web page provided in Markdown format inside `<markdown>` tags and extract the information requested in the `user_instructions`. You must process the content and return the extracted data in a strictly structured format, according to the requested output schema.</request>

    <additions>Focus exclusively on the textual content and its structure to identify the data. Ignore irrelevant elements such as script tags, styles, or metadata that do not contain the requested information. If a piece of information requested in `user_instructions` cannot be found in the Markdown content, the corresponding field in the output must be null or empty, as allowed by the schema. Be literal and precise in extraction, avoiding inferences or assumptions not directly supported by the text.</additions>
    
    <type>The output must be a single valid JSON object that exactly matches the provided data schema. Do not include any text, explanation, comment, or any character outside the JSON object. Your response must start with `{` and end with `}`.</type>
    
    <extras>Act as an automated extraction tool. Accuracy and schema compliance are your only priorities. Ensure that all required fields in the output schema are filled.</extras>
    """)
)

_PROMPT = Prompt.from_text(
    dedent("""\
    {{user_instructions}}

    <markdown>
    {{markdown}}
    </markdown>
    """)
)


# HTML -> MD -> LLM (Structured Output)
class Extractor(BaseModel):
    responder: Responder = Field(
        ..., description="The responder to use for the extractor."
    )
    reasoning: Reasoning | None = Field(default=None)
    model: str | None = Field(default=None)
    max_output_tokens: int | None = Field(default=None)

    @needs("playwright")
    async def extract_async[T: BaseModel](
        self,
        urls: Sequence[str],
        output: type[T],
        prompt: str | None = None,
        extraction_preferences: ExtractionPreferences | None = None,
        ignore_invalid_urls: bool = True,
    ) -> ExtractionResult[T]:
        from playwright import async_api

        _preferences = extraction_preferences or ExtractionPreferences()
        _actions: Sequence[Action] = _preferences.actions or []

        async with async_api.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for url in urls:
                await page.goto(url, timeout=10000)

                for action in _actions:
                    await action.execute(page)

            html = await page.content()
            markdown = convert(html)

            _prompt = _PROMPT.compile(
                user_instructions=prompt or "Not provided.", markdown=markdown
            )

            response = await self.responder.respond_async(
                input=_prompt,
                model=self.model,
                instructions=_INSTRUCTIONS,
                reasoning=self.reasoning,
                text_format=output,
            )

            return ExtractionResult[T](
                urls=urls,
                html=html,
                markdown=markdown,
                extraction_preferences=_preferences,
                result=response.output_parsed,
            )
