from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid

Base = declarative_base()

class BaseObject(BaseModel):
    id: Optional[str] = str(uuid.uuid4())
    # allow read from other object
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )