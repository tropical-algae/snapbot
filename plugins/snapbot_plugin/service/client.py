from pathlib import Path

from ncatbot.api import BotAPIClient
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent

from snapbot.common.logging import logger
from snapbot.core.tools.models import ToolArtifact, ToolArtifactKind

from ..model import SentGroupFile, SentMessageResult  # noqa: TID252


async def resolve_group_file_id(
    api: BotAPIClient,
    group_id: int | str,
    filename: str,
) -> str | None:
    try:
        file_list = await api.qq.query.get_group_root_files(group_id)
    except Exception:
        logger.warning(f"从群文件列表解析 file_id 失败: group_id={group_id}, filename={filename}")
        return None

    files = file_list.files or []

    candidates = [item for item in files if item.file_name == filename]
    candidates.sort(key=lambda item: item.upload_time or 0, reverse=True)
    return candidates[0].file_id if candidates else None


async def send_text(
    api: BotAPIClient,
    event: GroupMessageEvent | PrivateMessageEvent,
    text: str,
) -> SentMessageResult | None:
    text = text.strip().strip("\n")
    if not text:
        return None

    if event.is_group_msg():
        result = await api.qq.post_group_msg(event.group_id, text=text)
        return SentMessageResult(raw=result)

    result = await api.qq.post_private_msg(event.user_id, text=text)
    return SentMessageResult(raw=result)


async def send_message(
    api: BotAPIClient,
    event: GroupMessageEvent | PrivateMessageEvent,
    message: str | ToolArtifact,
) -> SentMessageResult | None:
    if isinstance(message, str):
        return await send_text(api, event, message)

    result = None
    sent_group_file: SentGroupFile | None = None
    if event.is_group_msg():
        if message.kind == ToolArtifactKind.IMAGE:
            result = await api.qq.send_group_image(event.group_id, message.path)
        elif message.kind == ToolArtifactKind.AUDIO:
            result = await api.qq.send_group_record(event.group_id, message.path)
        elif message.kind == ToolArtifactKind.VIDEO:
            result = await api.qq.send_group_video(event.group_id, message.path)
        elif message.kind == ToolArtifactKind.STICKER:
            result = await api.qq.send_group_sticker(event.group_id, message.path)
        else:
            result = await api.qq.send_group_file(event.group_id, message.path, message.name)
            filename = message.name or Path(message.path).name
            file_id = await resolve_group_file_id(api, event.group_id, filename)
            if file_id is None:
                logger.warning(f"文件已发送, 但未追踪到file id. group_id={event.group_id}, filename={filename}")
            else:
                sent_group_file = SentGroupFile(
                    group_id=event.group_id,
                    file_id=file_id,
                    name=filename,
                )
    else:
        if message.kind == ToolArtifactKind.IMAGE:
            result = await api.qq.send_private_image(event.user_id, message.path)
        elif message.kind == ToolArtifactKind.AUDIO:
            result = await api.qq.send_private_record(event.user_id, message.path)
        elif message.kind == ToolArtifactKind.VIDEO:
            result = await api.qq.send_private_video(event.user_id, message.path)
        elif message.kind == ToolArtifactKind.STICKER:
            result = await api.qq.send_private_sticker(event.user_id, message.path)
        else:
            result = await api.qq.send_private_file(event.user_id, message.path, message.name)

    if message.caption:
        await send_text(api, event, message.caption)

    return SentMessageResult(
        raw=result,
        group_file=sent_group_file,
    )


async def collect_message(api: BotAPIClient, event: GroupMessageEvent | PrivateMessageEvent) -> None:
    await api.qq.messaging.get_group_msg_history(
        group_id=event.group_id,
        message_seq=None,
        count=20,
    )


async def reply_emoji(api: BotAPIClient, event: GroupMessageEvent | PrivateMessageEvent) -> None:
    await api.qq.messaging.set_msg_emoji_like(
        message_id=event.message_id,
        emoji_id="1",
        set=True,
    )
