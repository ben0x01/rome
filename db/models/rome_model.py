from sqlalchemy import Column, Integer, String, Boolean, DateTime
from db.models.base_model import Base

class RomeLabs(Base):
    __tablename__ = "RomeLabs"
    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime, nullable=False)
    private_key = Column(String, nullable=False)
    proxy = Column(String, nullable=False)
    deploy_contract = Column(Boolean, nullable=False)
    deploy_tokens = Column(Boolean, nullable=False)
    transfer_tokens = Column(Boolean, nullable=False)
    swap = Column(Boolean, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    os_header = Column(String, nullable=False)
    chrome_version = Column(String, nullable=False)
    errors = Column(String, default=[])