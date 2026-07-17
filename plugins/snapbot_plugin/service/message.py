from ag_ui.core import ImageInputContent, InputContent, InputContentUrlSource, TextInputContent
from ncatbot.types import At, Image, MessageArray, PlainText


def build_agent_input_message(message: MessageArray, bot_user_id: int | str) -> list[InputContent]:
    bot_user_id = str(bot_user_id)
    filtered_message = MessageArray()
    content: list[InputContent] = []
    text_chunks: list[str] = []

    for segment in message.filter():
        if isinstance(segment, At) and segment.user_id == bot_user_id:
            continue
        if isinstance(segment, PlainText | At | Image):
            filtered_message.add_segment(segment)

    def append_text_content() -> None:
        if text_chunks:
            content.append(TextInputContent(text="".join(text_chunks)))
            text_chunks.clear()

    for segment in filtered_message.filter():
        if isinstance(segment, PlainText):
            if segment.text:
                text_chunks.append(segment.text)
        elif isinstance(segment, At):
            text_chunks.append(f"[CQ:at,qq={segment.user_id}]")
        elif isinstance(segment, Image):
            append_text_content()
            image_url = segment.to_attachment().url or segment.url or segment.file
            if image_url:
                content.append(ImageInputContent(source=InputContentUrlSource(value=image_url)))

    append_text_content()
    return content
