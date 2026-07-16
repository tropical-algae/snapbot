from secrets import token_urlsafe
from typing import Literal

from anyio import Path, TemporaryDirectory
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from snapbot.common.model import ToolArtifactType
from snapbot.common.utils.decorator import snap_tool
from snapbot.common.utils.file import generate_timestamp_filename, get_thread_workspace_path
from snapbot.common.utils.pdf import compress_and_encrypt_pdf
from snapbot.core.agent.models.agent import SubAgentName
from snapbot.core.toolkits.comic import jm_comic_toolkit
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind, ToolArtifactOutput

CompRatio = Literal["original", "high", "medium", "low"]
PDF_COMPRESS_PRESETS = {"low": (180, 80), "medium": (120, 60), "high": (90, 45)}


def get_pdf_compress_params(compress_ratio: CompRatio) -> tuple[int | None, int | None]:
    if compress_ratio == "original":
        return None, None
    try:
        return PDF_COMPRESS_PRESETS[compress_ratio]
    except KeyError as _:
        return None, None


class JmDownloadInput(BaseModel):
    album_id: str = Field(description="需要下载的 JM 本子 ID")
    encrypt: bool = Field(default=True, description="是否需要加密。默认加密")
    compress_ratio: CompRatio = Field(
        default="medium", description="压缩强度，强度越高文件越小、画质越低。original 表示不压缩。默认为 medium"
    )


@snap_tool(SubAgentName.COMIC_DOWNLOADER, args_schema=JmDownloadInput, produces_artifacts=True)
async def download_jm_album(
    config: RunnableConfig, album_id: str, encrypt: bool = True, compress_ratio: CompRatio = "medium"
) -> tuple[str, ToolArtifactOutput | None]:
    """根据 JM 漫画本子 ID 下载本子"""
    filename = f"jm_{album_id}_{generate_timestamp_filename()}"
    password = token_urlsafe(8) if encrypt else None
    dpi, quality = get_pdf_compress_params(compress_ratio)
    final_pdf_path = await get_thread_workspace_path(
        config=config,
        artifact_type=ToolArtifactType.CACHE,
        subdir="jm",
        filename=filename,
        ext="pdf",
    )
    try:
        async with TemporaryDirectory(prefix=f"{filename}_", dir=str(final_pdf_path.parent)) as temp_dir:
            temp_dir_path = Path(temp_dir)
            raw_pdf_path = await jm_comic_toolkit.download_album_pdf(
                album_id=album_id,
                pdf_dir=temp_dir_path / "pdf",
                image_dir=temp_dir_path / "images",
                filename=filename,
            )
            await compress_and_encrypt_pdf(raw_pdf_path, final_pdf_path, password, dpi, quality)
    except Exception as error:
        return f"下载失败：{error}", None

    return (
        f"JM 本子 {album_id} ({'未加密' if password is None else '已加密'})已成功下载",
        ToolArtifactOutput(
            artifacts=[
                ToolArtifact(
                    kind=ToolArtifactKind.FILE,
                    path=str(final_pdf_path),
                    name=final_pdf_path.name,
                    caption=f"PDF 密码: {password}" if password else None,
                    mime_type="application/pdf",
                )
            ],
            message="下载完成",
        ),
    )
