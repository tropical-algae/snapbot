from pydantic import BaseModel, Field


class VolcanoTTS(BaseModel):
    api_url: str = Field(default="https://openspeech.bytedance.com/api/v1/tts")
    cluster: str = Field(default="volcano_tts")

    app_id: str
    access_token: str
    voice_type: str


class ToolkitConfig(BaseModel):
    tavily_key: str
    volcano_tts: VolcanoTTS
    jm_option_file: str = Field(default="option.yml")
