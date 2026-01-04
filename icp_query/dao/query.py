from pydantic import BaseModel

from ..db.db import IcpRecord


class QueryResponse(BaseModel):
    cached: bool
    record: IcpRecord
