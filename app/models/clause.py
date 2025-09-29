# app/models/clause.py

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    tenant_id = Column(String, index=True, nullable=False)
    document_type = Column(String, default="contract")
    original_filename = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    clauses = relationship("Clause", back_populates="document")


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    clause_number = Column(String, index=True)  # 예: "제3조"
    clause_title = Column(String)  # 예: "계약의 해지"
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    document = relationship("Document", back_populates="clauses")
