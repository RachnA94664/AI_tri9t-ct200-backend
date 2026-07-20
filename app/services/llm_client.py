# import os
# import json
# from dotenv import load_dotenv
# # from huggingface_hub import InferenceClient
# from app.schemas.generation import TestCaseList

# load_dotenv()

# # Free-tier instruction-following model, good at structured JSON output
# MODEL = "meta-llama/Llama-3.1-8B-Instruct"

# SYSTEM_PROMPT = """You are a QA engineer generating test case ideas for a \
# medical device (blood pressure monitor) based on technical documentation. \
# You must respond with ONLY valid JSON, no prose, no markdown code fences, \
# matching exactly this schema:

# {
#   "test_cases": [
#     {
#       "id": "TC-1",
#       "title": "short descriptive title",
#       "steps": ["step 1", "step 2", "..."],
#       "expected_result": "what should happen"
#     }
#   ]
# }

# Generate between 3 and 5 test cases. Each test case must be concrete and \
# executable — reference specific values, thresholds, or error codes from \
# the provided text where relevant. Do not invent behavior not implied by \
# the text."""


# def _get_client() -> InferenceClient:
#     api_key = os.environ.get("HF_API_KEY")
#     if not api_key:
#         raise RuntimeError("HF_API_KEY not found in environment")
#     return InferenceClient(model=MODEL, token=api_key.strip())


# def call_llm(selection_text: str) -> dict:
#     client = _get_client()
#     response = client.chat_completion(
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": f"Source document text:\n\n{selection_text}"},
#         ],
#         max_tokens=1024,
#         temperature=0.3,
#     )
#     raw_content = response.choices[0].message.content
#     return _extract_json(raw_content)


# def _extract_json(raw_content: str) -> dict:
#     text = raw_content.strip()
#     if text.startswith("```"):
#         text = text.strip("`")
#         if text.startswith("json"):
#             text = text[4:]
#     return json.loads(text)


# def generate_test_cases(selection_text: str) -> TestCaseList:
#     last_error = None
#     for attempt in range(2):
#         try:
#             raw = call_llm(selection_text)
#             return TestCaseList(**raw)
#         except Exception as e:
#             last_error = e
#             continue
#     raise ValueError(f"LLM generation failed after retry: {last_error}") from last_error


import os
import json
from dotenv import load_dotenv
from groq import Groq
from app.schemas.generation import TestCaseList

load_dotenv()  # ensure .env is loaded even if this module runs before main.py's load_dotenv()

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a QA engineer generating test case ideas for a \
medical device (blood pressure monitor) based on technical documentation. \
You must respond with ONLY valid JSON, no prose, no markdown code fences, \
matching exactly this schema:

{
  "test_cases": [
    {
      "id": "TC-1",
      "title": "short descriptive title",
      "steps": ["step 1", "step 2", "..."],
      "expected_result": "what should happen"
    }
  ]
}

Generate between 3 and 5 test cases. Each test case must be concrete and \
executable — reference specific values, thresholds, or error codes from \
the provided text where relevant. Do not invent behavior not implied by \
the text."""


def _get_api_key() -> str:
    key = os.environ.get("GROQ_API")
    if not key:
        raise RuntimeError("GROQ_API not found in environment")
    key = key.strip()  # defensively strip whitespace/newlines from .env parsing
    print(f"DEBUG: using GROQ_API starting with {key[:12]}... (length={len(key)})")
    return key


def call_llm(selection_text: str) -> dict:
    """
    Explicitly passes api_key to the Groq client rather than relying on
    the SDK's implicit os.environ auto-detection, to eliminate any
    ambiguity about which key value is actually being sent.
    """
    api_key = _get_api_key()
    client = Groq(api_key=api_key)

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Source document text:\n\n{selection_text}"},
        ],
        temperature=0.3,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
    )
    raw_content = completion.choices[0].message.content
    return _extract_json(raw_content)


def _extract_json(raw_content: str) -> dict:
    text = raw_content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def generate_test_cases(selection_text: str) -> TestCaseList:
    last_error = None
    for attempt in range(2):
        try:
            raw = call_llm(selection_text)
            return TestCaseList(**raw)
        except Exception as e:
            last_error = e
            print(f"DEBUG: attempt {attempt} failed: {e}")
            continue
    raise ValueError(f"LLM generation failed after retry: {last_error}") from last_error



# # import os
# # import json
# # from groq import Groq
# # from app.schemas.generation import TestCaseList

# # MODEL = "llama-3.3-70b-versatile"  # confirm exact string via console.groq.com

# # SYSTEM_PROMPT = """You are a QA engineer generating test case ideas for a \
# # medical device (blood pressure monitor) based on technical documentation. \
# # You must respond with ONLY valid JSON, no prose, no markdown code fences, \
# # matching exactly this schema:

# # {
# #   "test_cases": [
# #     {
# #       "id": "TC-1",
# #       "title": "short descriptive title",
# #       "steps": ["step 1", "step 2", "..."],
# #       "expected_result": "what should happen"
# #     }
# #   ]
# # }

# # Generate between 3 and 5 test cases. Each test case must be concrete and \
# # executable — reference specific values, thresholds, or error codes from \
# # the provided text where relevant. Do not invent behavior not implied by \
# # the text."""


# # def call_llm(selection_text: str) -> dict:
# #     """
# #     Uses the official Groq SDK (reads GROQ_API_KEY from environment
# #     automatically — no need to pass it manually). Non-streaming here,
# #     since we need the full response to validate as JSON before returning
# #     anything — streaming doesn't make sense for structured-output
# #     validation.
# #     """
# #     client = Groq()  # reads GROQ_API_KEY from os.environ automatically
# #     print("client is working and ready to call LLM")
# #     completion = client.chat.completions.create(
# #         model=MODEL,
# #         messages=[
# #             {"role": "system", "content": SYSTEM_PROMPT},
# #             {"role": "user", "content": f"Source document text:\n\n{selection_text}"},
# #         ],
# #         temperature=0.3,
# #         max_completion_tokens=1024,
# #         top_p=1,
# #         stream=False,  # we need the full response at once to parse/validate
# #     )
# #     raw_content = completion.choices[0].message.content
# #     return _extract_json(raw_content)


# # def _extract_json(raw_content: str) -> dict:
# #     """LLMs sometimes wrap JSON in markdown fences or add stray prose
# #     despite instructions. Strip common wrappers before parsing."""
# #     text = raw_content.strip()
# #     if text.startswith("```"):
# #         text = text.strip("`")
# #         if text.startswith("json"):
# #             text = text[4:]
# #     return json.loads(text)  # raises json.JSONDecodeError if still malformed


# # def generate_test_cases(selection_text: str) -> TestCaseList:
# #     """
# #     Retry-once-then-fail-gracefully: LLM output can be malformed JSON,
# #     missing required fields, or too few/many test cases. We retry ONCE,
# #     then raise a clear error rather than looping indefinitely or silently
# #     returning garbage.
# #     """
# #     last_error = None
# #     for attempt in range(2):
# #         try:
# #             raw = call_llm(selection_text)
# #             return TestCaseList(**raw)  # Pydantic validates shape + count
# #         except Exception as e:
# #             last_error = e
# #             continue
# #     raise ValueError(f"LLM generation failed after retry: {last_error}") from last_error