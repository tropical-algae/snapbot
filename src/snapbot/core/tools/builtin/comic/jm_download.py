from secrets import token_urlsafe

from anyio import Path, TemporaryDirectory
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import generate_timestamp_filename, get_thread_workspace_path
from snapbot.common.utils.pdf import compress_and_encrypt_pdf
from snapbot.core.agent.models import RootAgentName
from snapbot.core.toolkits.comic import jm_comic_toolkit
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind, ToolArtifactOutput


class JmDownloadInput(BaseModel):
    album_id: str = Field(description="需要下载并导出为加密压缩 PDF 的 JM 本子 ID。")


@snap_tool(RootAgentName.SNAP_AGENT, args_schema=JmDownloadInput, produces_artifacts=True)
async def download_jm_album(album_id: str, config: RunnableConfig) -> tuple[str, ToolArtifactOutput]:
    """根据 JM 漫画本子 ID 下载本子，将其转换为压缩加密 PDF，并作为文件发送。"""
    filename = f"jm_{album_id}_{generate_timestamp_filename()}"
    password = token_urlsafe(8)
    final_pdf_path = await get_thread_workspace_path(
        config=config,
        artifact_type=ToolArtifactType.CACHE,
        subdir="jm",
        filename=filename,
        ext="pdf",
    )

    async with TemporaryDirectory(prefix=f"{filename}_", dir=str(final_pdf_path.parent)) as temp_dir:
        temp_dir_path = Path(temp_dir)
        raw_pdf_path = await jm_comic_toolkit.download_album_pdf(
            album_id=album_id,
            pdf_dir=temp_dir_path / "pdf",
            image_dir=temp_dir_path / "images",
            filename=filename,
        )
        await compress_and_encrypt_pdf(raw_pdf_path, final_pdf_path, password)

    caption = f"PDF 密码: {password}"
    return (
        f"JM 本子 {album_id} 已成功下载为加密 PDF。{caption}",
        ToolArtifactOutput(
            artifacts=[
                ToolArtifact(
                    kind=ToolArtifactKind.FILE,
                    path=str(final_pdf_path),
                    name=final_pdf_path.name,
                    caption=caption,
                    mime_type="application/pdf",
                )
            ],
            message="JM 本子下载完成。",
        ),
    )
