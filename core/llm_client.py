from groq import Groq
import config

_client = Groq(api_key=config.GROQ_API_KEY)

def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1024,
        temperature=0.2
    )
    return response.choices[0].message.content