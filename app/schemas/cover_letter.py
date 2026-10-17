from pydantic import BaseModel, Field


class CoverLetterOutput(BaseModel):
    """Structured output of the Cover Letter Writer agent."""

    cover_letter: str = Field(
        ..., description="The full cover letter body, ready to send"
    )
    word_count: int = Field(..., ge=0, description="Approximate word count")
    tone_used: str = Field(
        default="professional", description="Tone the letter was written in"
    )