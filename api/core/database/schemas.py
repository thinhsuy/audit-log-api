from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class LogEntryTable(BaseModel):
    __tablename__ = "logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String, index=True)
    resource_type = Column(String)
    resource_id = Column(Integer)
    user_id = Column(Integer)
    severity = Column(String)
    tenant_id = Column(String)
    timestamp = Column(String)