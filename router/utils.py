from pydantic import BaseModel
from typing import Optional, Literal


class CaptchaResponse(BaseModel):
    status: Literal["success", "error"]
    token: str
    time: Optional[float]


def make_response(captcha_key: str, time: float) -> CaptchaResponse:
    if captcha_key == "failed":
        return CaptchaResponse(status="error", token="")
    return CaptchaResponse(status="success", time=time, token=captcha_key)
