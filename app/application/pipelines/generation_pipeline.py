"""Chain-of-responsibility generation pipeline."""

from typing import Protocol

from app.application.pipelines.generation_context import GenerationContext


class GenerationStep(Protocol):
    """Single step in a generation pipeline."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Process and return updated context."""


class GenerationPipeline:
    """Run an ordered list of generation steps."""

    def __init__(self, steps: list[GenerationStep]) -> None:
        self._steps = steps

    async def run(self, context: GenerationContext) -> GenerationContext:
        """Execute all steps in order."""
        for step in self._steps:
            context = await step.process(context)
        return context
