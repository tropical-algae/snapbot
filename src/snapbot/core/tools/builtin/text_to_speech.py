from anyio import Path
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.configs import settings
from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import generate_timestamp_filename, get_thread_workspace_path
from snapbot.core.agent.models import RootAgentName
from snapbot.core.toolkits import volcano_text_to_speech
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind, ToolArtifactOutput

CACHE_PATH = Path(settings.agent.cache_path)
AUDIO_ENCODING = "mp3"


class TextToSpeechInput(BaseModel):
    text: str = Field(description="Text to be converted to speech.")


@snap_tool(RootAgentName.SNAPAGENT, args_schema=TextToSpeechInput, produces_artifacts=True)
async def text_to_speech(text: str, config: RunnableConfig) -> tuple[str, ToolArtifactOutput]:
    """Convert text into audio. When replying to users via voice, use this tool."""
    reqid = generate_timestamp_filename()
    filepath = await get_thread_workspace_path(
        config=config, artifact_type=ToolArtifactType.CACHE, subdir="tts", filename=reqid, ext=AUDIO_ENCODING
    )

    await volcano_text_to_speech(text, filepath, reqid, AUDIO_ENCODING)
    return (
        "Voice generated successfully.",
        ToolArtifactOutput(artifacts=[ToolArtifact(kind=ToolArtifactKind.AUDIO, path=str(filepath))]),
    )
