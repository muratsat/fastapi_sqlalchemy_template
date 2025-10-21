from pydantic import BaseModel


class OneTimeCodeInput(BaseModel):
    phone_number: str


class VerifyCodeInput(OneTimeCodeInput):
    name: str | None = None
    code: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AccessTokenSchema(BaseModel):
    access_token: str


class TokenPair(RefreshTokenSchema, AccessTokenSchema):
    pass
