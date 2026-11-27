from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class DispatchBoard(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaimOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Code


class SwapOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Code
    ply: Code


class ReportCaptures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Code
    actual: int
