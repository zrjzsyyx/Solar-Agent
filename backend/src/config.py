from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Data backend
    data_backend_url: str = "https://solar-system-mon.preview.aliyun-zeabur.cn"

    # Agent
    agent_port: int = 9000
    alert_poll_interval_sec: int = 60


settings = Settings()
