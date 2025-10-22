import phonenumbers
from pydantic import BaseModel, field_validator


class OneTimeCodeInput(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            # Return in E.164 format for consistency
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")


class VerifyCodeInput(OneTimeCodeInput):
    name: str | None = None
    code: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AccessTokenSchema(BaseModel):
    access_token: str


class TokenPair(RefreshTokenSchema, AccessTokenSchema):
    pass
