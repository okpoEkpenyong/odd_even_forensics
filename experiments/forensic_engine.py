import os
import re
import time
import logging
from datetime import datetime, timezone
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODELS = {
    "GPT120B_OSS": "openai/gpt-oss-120b",
    "GPT20B_OSS": "openai/gpt-oss-20b",
}

TEMPERATURE = 1
REASONING_EFFORT = "medium"
MAX_RETRIES = 3


def parse_number(answer: str):
    """Extract the last integer in the answer (survives prose like 'here is **42**')."""
    matches = re.findall(r'-?\d+', answer or "")
    return int(matches[-1]) if matches else None


_BARE_NUM_RE = re.compile(r'^\s*-?\d+\s*[.!]?\s*$')
_ANY_NUM_RE  = re.compile(r'-?\d+')
_BOLD_NUM_RE = re.compile(r'\*\*\s*(-?\d+)\s*\*\*')

def parse_number_strict(answer: str) -> dict:
    """
    Returns a dict with the parsed number plus a confidence/flag field,
    instead of silently guessing.
    """
    text = (answer or "").strip()
    if not text:
        return {"number": None, "confidence": "empty", "all_numbers": []}

    all_numbers = [int(m) for m in _ANY_NUM_RE.findall(text)]

    # Case 1: answer is *just* a number (highest confidence)
    if _BARE_NUM_RE.match(text):
        return {"number": all_numbers[0], "confidence": "bare", "all_numbers": all_numbers}

    # Case 2: answer has exactly one bolded number, e.g. "**42**"
    bold_matches = _BOLD_NUM_RE.findall(text)
    if len(bold_matches) == 1:
        return {"number": int(bold_matches[0]), "confidence": "bolded", "all_numbers": all_numbers}

    # Case 3: exactly one number anywhere in the text — safe to take it
    if len(all_numbers) == 1:
        return {"number": all_numbers[0], "confidence": "unique", "all_numbers": all_numbers}

    # Case 4: multiple numbers, no bold disambiguation — DO NOT GUESS
    if len(all_numbers) > 1:
        return {"number": None, "confidence": "ambiguous_multi", "all_numbers": all_numbers}

    # Case 5: no numbers found at all (e.g. refusal, non-numeric text)
    return {"number": None, "confidence": "no_number", "all_numbers": []}    


class ForensicEngine:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
    def _chat(self, model, messages):
        """Bare chat call, no parsing/frame-tagging — used by callers that
        need a raw follow-up completion (e.g. the awareness-pushback probe
        in odd_even_persona_hierarchy_test.py), distinct from
        run_forensic_task which additionally parses the answer into a
        structured row. Shares the same retry/backoff behavior as
        run_forensic_task for consistency.
        """
        for attempt in range(MAX_RETRIES):
            try:
                res = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=TEMPERATURE,
                    top_p=1,
                    reasoning_effort=REASONING_EFFORT,
                )
                msg = res.choices[0].message
                cot = getattr(msg, "reasoning", None) or ""
                answer = msg.content or ""
                return cot, answer
            except Exception as e:
                wait = 2 ** attempt * 5
                logging.warning(f"_chat attempt {attempt+1} failed ({e}); retrying in {wait}s")
                time.sleep(wait)
        logging.error(f"_chat: skipped after {MAX_RETRIES} failures")
        return None, None
    
    def run_forensic_task(self, model_key, system_prompt, user_content):
        model = MODELS[model_key]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        for attempt in range(MAX_RETRIES):
            try:
                res = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=TEMPERATURE,
                    top_p=1,
                    reasoning_effort=REASONING_EFFORT,
                )
                msg = res.choices[0].message
                cot = getattr(msg, "reasoning", None) or ""
                answer = msg.content or ""
                #number = parse_number_strict(answer)
                result = parse_number_strict(answer)
                number = result["number"]
                return {
                    "cot": cot,
                    "answer": answer,
                    "parsed_number": number,
                    "is_odd": (number % 2 != 0) if number is not None else None,
                    "model": model,
                    "temperature": TEMPERATURE,
                    "reasoning_effort": REASONING_EFFORT,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                wait = 2 ** attempt * 5
                logging.warning(f"Attempt {attempt+1} failed ({e}); retrying in {wait}s")
                time.sleep(wait)
        logging.error(f"Skipped run after {MAX_RETRIES} failures: {model_key}")
        return None  # caller skips; never written as a data row