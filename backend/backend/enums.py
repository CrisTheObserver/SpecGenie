from enum import Enum

class LLMEnum(str, Enum):
    GEMINI = "gemini"
    CHATGPT = "gpt"

class RoleEnum(str, Enum):
    MAKER = "Maker"
    JUDGE = "Judge"
    COPYWRITER = "Copywriter"

class LangEnum(str, Enum):
    ENGLISH = "en"
    ESPAÑOL = "es"