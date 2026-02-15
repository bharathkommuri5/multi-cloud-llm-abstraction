from fastapi import APIRouter, HTTPException
from app.schemas.request import LLMRequest
from app.schemas.response import LLMResponse
from app.llm.factory import get_llm_client

router = APIRouter()


@router.post("/generate", response_model=LLMResponse)
def generate_text(request: LLMRequest):
    try:
        client = get_llm_client(request.provider)

        result = client.generate(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        return LLMResponse(provider=request.provider, response=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
