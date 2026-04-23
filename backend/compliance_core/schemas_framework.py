from pydantic import BaseModel, Field


class FrameworkIngestBody(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    framework: str = Field(min_length=1, max_length=128)
    version: str = Field(default="1.0", max_length=64)
    jurisdiction: str | None = Field(default=None, max_length=64)
    text: str = Field(min_length=1, description="Full policy or framework text to chunk and index")
