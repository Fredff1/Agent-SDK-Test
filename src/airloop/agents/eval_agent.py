from pydantic import BaseModel
from agents import Agent


class EvalScores(BaseModel):
    helpfulness: float
    usefulness: float
    fluency: float
    instruction_follow: float
    overall: float
    reasoning: str | None = None


EVAL_PROMPT = """
You are an evaluation assistant. Given the user request, assistant reply, and optional expected answer, score the reply on multiple dimensions.
Return ONLY valid JSON with the fields below (scores 0-5, floats allowed):
{
  "helpfulness": number,
  "usefulness": number,
  "fluency": number,
  "instruction_follow": number,
  "overall": number,
  "reasoning": "short rationale"
}
"""


def build_eval_agent(model) -> Agent:
    return Agent(
        name="LLM Judge",
        model=model,
        instructions=EVAL_PROMPT,
        output_type=EvalScores,
    )
