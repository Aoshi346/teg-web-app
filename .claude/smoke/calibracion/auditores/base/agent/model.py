"""Factoría única del modelo del bot: proveedor, modelo y etiquetas en un solo sitio."""
from langchain.chat_models import init_chat_model

DEFAULT_MODEL = "openai:gpt-4o-mini"


def get_model(temperature: float = 0.0):
    return init_chat_model(DEFAULT_MODEL, temperature=temperature).with_config(
        tags=["shop-bot"], run_name="shop-bot"
    )
