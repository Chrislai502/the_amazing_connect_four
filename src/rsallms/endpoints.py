
import importlib.resources

from dataclasses import dataclass
from typing import Callable
from os import environ as env

import chevron
import requests

import dotenv
try:
    dotenv.load_dotenv()
except:
    print(f"Could not load environment variables. Continuing without them ...")

PROMPTS_FOLDER = importlib.resources.files("rsallms").joinpath("prompts")


@dataclass
class Endpoint:
    """
    Common interface for interacting with an OAI API endpoint (e.g. ollama, groq, etc.)

    :param base_url: the base URL of the API
    :param model: the model to use for the chat completion endpoint
    :param api_key: (optional) the api key necessary to complete requests
    """

    DEFAULTS = {
        "oai": {
            "base_url": "https://api.openai.com/",
            "api_key": "OPENAI_API_KEY"
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/",
            "api_key": "GROQ_API_KEY"
        }
    }

    base_url: str
    model: str
    api_key: str | None = None

    CHAT_COMPLETION = "v1/chat/completions"

    def __post_init__(self):
        # resolve commonly used endpoints
        if self.base_url in Endpoint.DEFAULTS:
            info = Endpoint.DEFAULTS[self.base_url]
            self.base_url = info["base_url"]

            api_key_env_var = info["api_key"]
            if api_key_env_var not in env:
                raise OSError(f"API Key {api_key_env_var} not found!")
            self.api_key = env[api_key_env_var]

    @property
    def chat_url(self):
        return f"{self.base_url}/{Endpoint.CHAT_COMPLETION}"

    def respond(self, message: str, system_prompt: str | None = None) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key is not None:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = [{"role": "user", "content": message}]
        if system_prompt is not None:
            messages.insert(0, {"role": "system", "content": system_prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        response = requests.post(self.chat_url, headers=headers, json=data)

        try:
            json_response = response.json()
        except Exception as e:
            print(response.text)
            raise e

        if 'error' in json_response:
            raise ValueError(f"Error in endpoint request!: {json_response['error']}")
        if 'choices' not in json_response:
            raise ValueError(f"Malformed response from endpoint!: Got: {json_response}")

        return json_response['choices'][0]['message']['content']


class CannedResponder(Endpoint):
    def __init__(self, responder_func: Callable[[str, str | None], str]):
        super().__init__("", "")
        self.responder = responder_func

    def respond(self, message, system_prompt=None):
        return self.responder(message, system_prompt)


def get_prompt(name: str, **kwargs) -> str:
    with PROMPTS_FOLDER.joinpath(f"{name}.mustache").open() as f:
        return chevron.render(f.read(), data=kwargs).strip()


def chain_prompts(files: list[str], **kwargs) -> str:
    content = []
    for file in files:
        content.append(get_prompt(file, **kwargs))
    return "\n".join(content)
