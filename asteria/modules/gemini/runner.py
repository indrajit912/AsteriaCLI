"""
Gemini API runner for AsteriaCLI.

This module handles the actual communication with the Gemini API.
It is designed to be swappable — replace this file to use a different
backend (LangChain, Vertex AI, local Ollama, etc.) without touching
any other module.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from pathlib import Path
from typing import Optional

from asteria.config.manager import get_config
from asteria.exceptions import GeminiAPIError, GeminiRunnerError

logger = logging.getLogger("asteria.modules.gemini.runner")


class GeminiRunner:
    """Executes prompts against the Gemini API.

    This class is intentionally minimal and decoupled so that swapping
    the underlying API client is a single-file change.

    Attributes:
        api_key: Gemini API key.
        model: Gemini model name.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """Initialise the runner from config or explicit arguments.

        Args:
            api_key: Optional API key override.
            model: Optional model name override.
        """
        config = get_config()
        self.api_key = api_key or config.gemini_api_key
        self.model = model or config.gemini_model
        self._client = None  # Lazy-loaded

    def _get_client(self):  # type: ignore
        """Lazy-load the google-genai client.

        Returns:
            Configured client instance.

        Raises:
            GeminiAPIError: If the API key is missing or the library fails.
        """
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise GeminiAPIError(
                "Gemini API key is not configured. "
                "Run: asteria config set gemini.api_key YOUR_KEY"
            )

        try:
            from google import genai  # type: ignore
            self._client = genai.Client(api_key=self.api_key)
            logger.debug("Gemini client initialised with model: %s", self.model)
            return self._client
        except ImportError as exc:
            raise GeminiAPIError(
                "google-genai is not installed. "
                "Run: pip install google-genai"
            ) from exc
        except Exception as exc:
            raise GeminiAPIError(f"Failed to initialise Gemini client: {exc}") from exc

    def run_prompt_text(self, prompt_text: str) -> str:
        """Send raw prompt text to the Gemini API and return the response.

        Args:
            prompt_text: The prompt string to send.

        Returns:
            The API response text.

        Raises:
            GeminiAPIError: If the API call fails.
        """
        client = self._get_client()
        try:
            logger.debug("Sending prompt (%d chars) to Gemini", len(prompt_text))
            # Use the new google-genai client API
            response = client.models.generate_content(
                model=self.model,
                contents=prompt_text,
            )
            result = response.text
            logger.debug("Received response (%d chars)", len(result))
            return result
        except Exception as exc:
            raise GeminiAPIError(f"Gemini API error: {exc}") from exc

    def run_prompt_file(
        self,
        prompt_path: Path,
        output_path: Path,
    ) -> str:
        """Read a prompt file, call the API, and write output to a file.

        Args:
            prompt_path: Path to the prompt .txt file.
            output_path: Path where the response will be written.

        Returns:
            The API response text.

        Raises:
            GeminiRunnerError: If the prompt file cannot be read.
            GeminiAPIError: If the API call fails.
        """
        if not prompt_path.exists():
            raise GeminiRunnerError(
                f"Prompt file not found: {prompt_path}"
            )

        try:
            prompt_text = prompt_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise GeminiRunnerError(
                f"Cannot read prompt file: {exc}"
            ) from exc

        if not prompt_text.strip():
            raise GeminiRunnerError(
                f"Prompt file is empty: {prompt_path}"
            )

        response_text = self.run_prompt_text(prompt_text)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response_text, encoding="utf-8")
        logger.info("Output written to: %s", output_path)

        return response_text
