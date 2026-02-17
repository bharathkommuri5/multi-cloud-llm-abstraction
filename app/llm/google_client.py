from app.core.config import settings
from app.llm.base import BaseLLMClient
from app.core.exceptions import LLMProviderError

# Support both old `google.generativeai` and new `google.genai` packages
try:
    import google.genai as genai  # new package
    _NEW_GENAI = True
except Exception:
    try:
        import google.generativeai as genai  # deprecated package (fallback)
        _NEW_GENAI = False
    except Exception:
        genai = None
        _NEW_GENAI = False


class GoogleLLMClient(BaseLLMClient):

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise LLMProviderError("Google API Key is not configured")
        # configure depending on package
        if genai is None:
            raise LLMProviderError("Google Generative AI client library is not installed")

        if _NEW_GENAI:
            # new genai client
            try:
                self.client = genai.Client()
                # some versions support specifying api_key via env or client; fall back to configure if available
                if hasattr(genai, "configure"):
                    try:
                        genai.configure(api_key=settings.GOOGLE_API_KEY)
                    except Exception:
                        pass
            except Exception:
                # Try module-level configure (older behavior)
                if hasattr(genai, "configure"):
                    genai.configure(api_key=settings.GOOGLE_API_KEY)
                    self.client = None
                else:
                    raise LLMProviderError("Unable to initialize google.genai client")
        else:
            # older package
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.client = None

        self.model = settings.GOOGLE_MODEL_ID or "gemini-pro"

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        try:
            if _NEW_GENAI:
                # prefer client.generate_text if available
                if getattr(self, "client", None) is not None and hasattr(self.client, "generate_text"):
                    response = self.client.generate_text(
                        model=self.model,
                        input=prompt,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                else:
                    # try module-level generate_text
                    if hasattr(genai, "generate_text"):
                        response = genai.generate_text(
                            model=self.model,
                            input=prompt,
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        )
                    else:
                        raise LLMProviderError("Installed google.genai package does not expose a supported generate API")

                # extract text
                if hasattr(response, "text") and response.text:
                    return response.text
                # fallback to inspect output structure
                out = getattr(response, "output", None)
                if out:
                    # try common shapes
                    try:
                        if isinstance(out, list) and len(out) > 0:
                            first = out[0]
                            if isinstance(first, dict) and "content" in first:
                                # content may be a list of dicts
                                content = first.get("content")
                                if isinstance(content, list) and len(content) > 0:
                                    txt = content[0].get("text") or content[0].get("text")
                                    if txt:
                                        return txt
                    except Exception:
                        pass

                raise LLMProviderError("Empty response from Google Generative AI")
            else:
                # older `google.generativeai` usage
                model = genai.GenerativeModel(self.model)

                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )

                if response.text:
                    return response.text
                else:
                    raise LLMProviderError("Empty response from Google Generative AI")
                
        except Exception as e:
            raise LLMProviderError(f"Google Generative AI error: {str(e)}")
