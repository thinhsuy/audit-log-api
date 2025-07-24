from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
import uuid

Base = declarative_base()

class BaseObject(BaseModel):
    # use default factory to renew id every instance created
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True