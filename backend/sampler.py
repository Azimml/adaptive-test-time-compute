import asyncio
from openai import AsyncOpenAI
from backend.config import OPENAI_API_KEY, MODEL, TEMPERATURE, MAX_TOKENS

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "You are a precise math problem solver. Solve the problem step by step, "
    "showing your reasoning clearly. At the very end of your response, write "
    "your final numerical answer after 'The answer is'. "
    "Example ending: 'The answer is 42'"
)


async def generate_sample(question: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        return {
            "reasoning": content,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
    except Exception as e:
        return {
            "reasoning": f"[API Error: {str(e)}]",
            "input_tokens": 0,
            "output_tokens": 0,
        }


async def generate_samples(question: str, n: int) -> list[dict]:
    tasks = [generate_sample(question) for _ in range(n)]
    return await asyncio.gather(*tasks)
