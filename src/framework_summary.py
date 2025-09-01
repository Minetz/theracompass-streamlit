"""Framework summary class."""

from enum import Enum

from pydantic import BaseModel

from firebase_handler import delete_json, load_json, save_json


class TherapyFramework(str, Enum):
    """Enumeration of supported therapy frameworks."""

    cbt = "cognitive behavioral therapy"
    dbt = "dialectical behavior therapy"
    act = "acceptance and commitment therapy"


class BasicSummary(BaseModel):
    """LLM output schema containing just the summary text."""

    summary: str


class FrameworkSummary(BaseModel):
    """Stored framework-based summary."""

    framework: str
    summary: str

    @staticmethod
    def load_summary(transcription_id: str) -> "FrameworkSummary | None":
        """Load a framework summary from storage."""
        data = load_json("framework_summaries", transcription_id)
        if data:
            return FrameworkSummary(**data)
        return None

    @staticmethod
    def save_summary(transcription_id: str, summary: "FrameworkSummary") -> None:
        """Save a framework summary to storage."""
        save_json("framework_summaries", transcription_id, summary.model_dump())

    @staticmethod
    def delete_summary(transcription_id: str) -> bool:
        """Delete a stored framework summary."""
        return delete_json("framework_summaries", transcription_id)
