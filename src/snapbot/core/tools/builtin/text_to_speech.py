from anyio import Path
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.configs import settings
from snapbot.common.utils.decorator import snap_tool
from snapbot.core.agent.models import RootAgentName
from snapbot.core.toolkits import volcano_text_to_speech
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind, ToolArtifactOutput

CACHE_PATH = Path(settings.agent.cache_path)


class TextToSpeechInput(BaseModel):
    text: str = Field(description="Text to be converted to speech.")


@snap_tool(RootAgentName.SNAPAGENT, args_schema=TextToSpeechInput, produces_artifacts=True)
async def text_to_speech(text: str, config: RunnableConfig) -> tuple[str, ToolArtifactOutput]:
    """Convert text into audio. When replying to users via voice, use this tool."""

    configurable = config.get("configurable", {})
    thread_id: str = configurable.get("thread_id", "none-thread")
    output_path = CACHE_PATH / thread_id / "tts"
    await output_path.mkdir(parents=True, exist_ok=True)

    filepath: Path = await volcano_text_to_speech(text, output_path)
    abs_filepath = str(await filepath.absolute())
    return (
        "Voice generated successfully.",
        ToolArtifactOutput(artifacts=[ToolArtifact(kind=ToolArtifactKind.AUDIO, path=abs_filepath)]),
    )
