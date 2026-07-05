import base64

import httpx
from anyio import Path

from snapbot.common.configs import settings
from snapbot.common.utils.file import generate_timestamp_filename

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer;{settings.toolkits.volcano_tts.access_token}",
}
APP = {
    "appid": settings.toolkits.volcano_tts.app_id,
    "token": settings.toolkits.volcano_tts.access_token,
    "cluster": settings.toolkits.volcano_tts.cluster,
}
AUDIO_ENCODING = "mp3"


async def volcano_text_to_speech(
    text: str,
    output_path: str,
    speed_ratio: float = 1.0,
    volume_ratio: float = 1.0,
    pitch_ratio: float = 1.0,
) -> Path:
    reqid = generate_timestamp_filename()

    payload = {
        "app": APP,
        "user": {
            "uid": "snapbot-user",
        },
        "audio": {
            "voice_type": settings.toolkits.volcano_tts.voice_type,
            "encoding": AUDIO_ENCODING,
            "speed_ratio": speed_ratio,
            "volume_ratio": volume_ratio,
            "pitch_ratio": pitch_ratio,
        },
        "request": {
            "reqid": reqid,
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            settings.toolkits.volcano_tts.api_url,
            headers=HEADERS,
            json=payload,
        )

    resp.raise_for_status()
    result: dict = resp.json()

    if result.get("code") != 3000:
        raise RuntimeError(f"TTS failed: code={result.get('code')}, message={result.get('message')}, raw={result}")

    audio_base64 = result.get("data")
    if not audio_base64:
        raise RuntimeError(f"TTS response has no audio data: {result}")

    audio_bytes = base64.b64decode(audio_base64)

    output_file = Path(output_path) / f"{reqid}.{AUDIO_ENCODING}"
    await output_file.write_bytes(audio_bytes)
    return output_file
