"""
gemini_service.py
-----------------
Wrapper around the Google Gen AI SDK (google-genai >= 1.0).

All three planners call generate_recommendation() to get AI responses.
This module handles:
  - Client initialisation (once, on first call)
  - Text-only and multimodal (text + image) requests
  - JSON extraction and parsing from the response
  - Automatic retry with exponential backoff for transient 503/429 errors
  - Graceful error handling — never raises to the caller

SDK reference: https://googleapis.github.io/python-genai/
Error classes:  google.genai.errors.ServerError / ClientError (inherit from APIError)
                APIError.code  → HTTP status int  (e.g. 503)
                APIError.status → status string    (e.g. "UNAVAILABLE")
                APIError.message → human message
"""

import json
import re
import time
import logging
import traceback
from typing import Optional

print("[GEMINI_SERVICE] module importing google.genai ...")  # proves THIS file is loaded
from google import genai
from google.genai import types, errors as genai_errors
print("[GEMINI_SERVICE] google.genai imported successfully")

import config

logger = logging.getLogger(__name__)

print(f"[GEMINI_SERVICE] config loaded — model={config.GEMINI_MODEL}, "
      f"key_set={'YES' if config.GEMINI_API_KEY else 'NO'}")

# ── Retry settings ─────────────────────────────────────────────────────────
_MAX_RETRIES = 3            # total attempts (1 original + 2 retries)
_RETRY_DELAYS = [2, 4, 8]  # seconds to wait before attempt 2, 3, 4
_RETRYABLE_CODES = {503, 429}  # 503 = overloaded, 429 = rate-limited

# ── Gemini client — initialised lazily on first call ──────────────────────
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Return the cached genai.Client, creating it on first call."""
    global _client
    if _client is None:
        print("[GEMINI_SERVICE] _get_client: creating genai.Client ...")
        try:
            _client = genai.Client(api_key=config.GEMINI_API_KEY)
            print("[GEMINI_SERVICE] _get_client: genai.Client created OK")
        except Exception as _init_exc:
            print(f"[GEMINI_SERVICE] _get_client: FAILED to create client: "
                  f"{type(_init_exc).__name__}: {_init_exc}")
            traceback.print_exc()
            raise
    else:
        print("[GEMINI_SERVICE] _get_client: reusing existing client")
    return _client


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception is a transient server-side error worth retrying."""
    if isinstance(exc, genai_errors.ServerError):
        return exc.code in _RETRYABLE_CODES
    return False


# ── JSON extraction helpers ────────────────────────────────────────────────

def _extract_json(text: str) -> Optional[dict]:
    """
    Try multiple strategies to extract a JSON object from the response text.

    Strategy 1: Direct json.loads (ideal — model returns pure JSON).
    Strategy 2: Strip markdown code fences (```json ... ```) then parse.
    Strategy 3: Regex scan for the first {...} block in the text.

    Returns the parsed dict, or None if all strategies fail.
    """
    # Strategy 1: direct parse
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: strip markdown fences
    stripped = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 3: extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ── Internal single-attempt caller ────────────────────────────────────────

def _call_gemini(
    client: genai.Client,
    contents,
    gen_config: types.GenerateContentConfig,
) -> dict:
    """
    Make one generate_content call and return a parsed dict.
    Raises genai_errors.ServerError / ClientError on API failure.
    Returns {"error": True, ...} only for empty/unparseable responses.
    """
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=gen_config,
    )

    if not response or not response.text:
        logger.warning("Gemini returned an empty response.")
        return {
            "error": True,
            "message": (
                "The AI did not return a response. "
                "Please try again or adjust your inputs."
            ),
        }

    result = _extract_json(response.text)
    if result is None:
        logger.warning(
            "Could not parse JSON from Gemini response: %s",
            response.text[:500],
        )
        return {
            "error": True,
            "message": "The AI response could not be processed. Please try again.",
            "raw_response": response.text[:1000],
        }

    return result


# ── Public API ─────────────────────────────────────────────────────────────

def generate_recommendation(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    image_mime_type: str = "image/jpeg",
) -> dict:
    """
    Send a prompt (and optionally an image) to Gemini and return parsed JSON.

    Automatically retries up to _MAX_RETRIES times on 503/429 responses,
    waiting _RETRY_DELAYS[attempt] seconds between each attempt.

    Parameters
    ----------
    prompt : str
        The full structured prompt built by prompt_builder.py.
    image_bytes : bytes | None
        Raw image bytes for multimodal requests (jewelry planner).
        If None, a text-only request is made.
    image_mime_type : str
        MIME type of the image. Accepted: "image/jpeg", "image/png", "image/webp".

    Returns
    -------
    dict
        On success : the parsed recommendation dict from Gemini.
        On failure : {"error": True, "message": "<human-readable description>"}
    """
    try:
        client = _get_client()

        # ── Build contents ─────────────────────────────────────────────────
        if image_bytes:
            contents = [
                types.Part.from_bytes(data=image_bytes, mime_type=image_mime_type),
                types.Part.from_text(text=prompt),
            ]
        else:
            contents = prompt

        # ── Generation config ──────────────────────────────────────────────
        # NOTE: gemini-3.8-flash does not support temperature / top_p / top_k.
        gen_config = types.GenerateContentConfig(
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        # ── Diagnostics ────────────────────────────────────────────────────
        key = config.GEMINI_API_KEY or ""
        masked_key = (key[:8] + "..." + key[-4:]) if len(key) > 12 else "*** too short ***"
        print(f"\n[GEMINI DEBUG] API key loaded : {masked_key}")
        print(f"[GEMINI DEBUG] Model          : {config.GEMINI_MODEL}")
        print(f"[GEMINI DEBUG] Has image      : {image_bytes is not None}")
        if isinstance(contents, str):
            print(f"[GEMINI DEBUG] Contents type  : plain string ({len(contents)} chars)")
        else:
            print(f"[GEMINI DEBUG] Contents type  : list of {len(contents)} part(s)")

        # ── Retry loop ─────────────────────────────────────────────────────
        last_exc: Optional[Exception] = None

        for attempt in range(1, _MAX_RETRIES + 1):
            print(f"[GEMINI DEBUG] Attempt {attempt}/{_MAX_RETRIES} — calling generate_content ...")
            try:
                result = _call_gemini(client, contents, gen_config)
                print(f"[GEMINI DEBUG] Attempt {attempt} succeeded.")
                return result

            except genai_errors.ServerError as exc:
                last_exc = exc
                print(f"[GEMINI DEBUG] Attempt {attempt} — ServerError: "
                      f"code={exc.code} status={exc.status} message={exc.message}")

                if _is_retryable(exc) and attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS[attempt - 1]
                    print(f"[GEMINI DEBUG] Retryable error (HTTP {exc.code}). "
                          f"Waiting {delay}s before attempt {attempt + 1} ...")
                    time.sleep(delay)
                    continue

                # Non-retryable server error, or retries exhausted
                raise

            except genai_errors.ClientError as exc:
                # Client errors (4xx) are never retried — they indicate a bad request
                last_exc = exc
                raise

        # Should not reach here, but guard anyway
        raise last_exc  # type: ignore[misc]

    except genai_errors.ServerError as exc:
        # ── Detailed terminal output ───────────────────────────────────────
        print(f"\n[GEMINI ERROR] ServerError — code={exc.code} status={exc.status}")
        print(f"[GEMINI ERROR] Message : {exc.message}")
        if exc.__cause__ is not None:
            print(f"[GEMINI ERROR] Caused by: {type(exc.__cause__).__name__}: {exc.__cause__}")
        print("[GEMINI ERROR] Full traceback:")
        traceback.print_exc()
        print("[GEMINI ERROR] --- end ---\n")
        logger.error("Gemini ServerError %s: %s", exc.code, exc.message)

        # ── User-facing message depends on status code ─────────────────────
        if exc.code == 503:
            return {
                "error": True,
                "message": (
                    "Gemini is temporarily busy. Please try again in a moment."
                ),
            }
        if exc.code == 500:
            return {
                "error": True,
                "message": (
                    "Gemini encountered an internal error. Please try again."
                ),
            }
        return {
            "error": True,
            "message": f"Gemini returned a server error ({exc.code}). Please try again.",
        }

    except genai_errors.ClientError as exc:
        print(f"\n[GEMINI ERROR] ClientError — code={exc.code} status={exc.status}")
        print(f"[GEMINI ERROR] Message : {exc.message}")
        print("[GEMINI ERROR] Full traceback:")
        traceback.print_exc()
        print("[GEMINI ERROR] --- end ---\n")
        logger.error("Gemini ClientError %s: %s", exc.code, exc.message)

        if exc.code == 401 or exc.code == 403:
            return {
                "error": True,
                "message": (
                    "Gemini API authentication failed. "
                    "Please check your API key and try again."
                ),
            }
        return {
            "error": True,
            "message": (
                f"The request to Gemini was invalid ({exc.code}: {exc.status}). "
                "Please check your inputs and try again."
            ),
        }

    except Exception as exc:  # noqa: BLE001
        err_name = type(exc).__name__
        err_str = str(exc)
        print(f"\n[GEMINI ERROR] Unexpected exception — {err_name}: {err_str}")
        if exc.__cause__ is not None:
            print(f"[GEMINI ERROR] Caused by: {type(exc.__cause__).__name__}: {exc.__cause__}")
        print("[GEMINI ERROR] Full traceback:")
        traceback.print_exc()
        print("[GEMINI ERROR] --- end ---\n")
        logger.error("Gemini unexpected error [%s]: %s", err_name, err_str, exc_info=True)

        return {
            "error": True,
            "message": (
                f"An unexpected error occurred ({err_name}). "
                "Please try again."
            ),
        }
