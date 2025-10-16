from pydantic import BaseModel


class OneTimeCodeInput(BaseModel):
    phone_number: str


class VerifyCodeInput(OneTimeCodeInput):
    name: str | None = None
    code: str


class Token(BaseModel):
    access_token: str
    token_type: str
