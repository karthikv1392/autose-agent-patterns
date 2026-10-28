"""Minimal agent: a name + a persona + one LLM call.

Multi-agent patterns differ in HOW agents are wired together, not in what a single
agent is, so we keep the agent itself deliberately tiny.
"""

from dataclasses import dataclass

from shared.llm import generate


@dataclass
class Agent:
    name: str
    persona: str                 # system prompt: shapes this agent's reasoning style
    temperature: float = 0.3

    def ask(self, prompt: str) -> str:
        return generate(prompt, system=self.persona, temperature=self.temperature)
