from sqlalchemy import Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from .db import db

class Document(db.Model):
    __tablename__ = 'documents'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_image_path: Mapped[str] = mapped_column(Text, nullable=False)
    enhanced_image_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(50), default='uploaded')

    # Relationships
    characters: Mapped[List["Character"]] = relationship("Character", back_populates="document", cascade="all, delete-orphan")
    lines: Mapped[List["Line"]] = relationship("Line", back_populates="document", cascade="all, delete-orphan")
    batch_results: Mapped[List["BatchResult"]] = relationship("BatchResult", back_populates="document")

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_image_path': self.original_image_path,
            'enhanced_image_path': self.enhanced_image_path,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'status': self.status
        }


class Character(db.Model):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey('documents.id'), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="characters")

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'image_path': self.image_path,
            'bbox': {
                'x': self.bbox_x,
                'y': self.bbox_y,
                'w': self.bbox_w,
                'h': self.bbox_h
            },
            'label': self.label,
            'group_id': self.group_id,
            'is_valid': self.is_valid
        }


class Line(db.Model):
    __tablename__ = 'lines'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey('documents.id'), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    line_order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bbox_y_start: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y_end: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="lines")

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'image_path': self.image_path,
            'line_order': self.line_order,
            'text': self.text,
            'bbox_y_start': self.bbox_y_start,
            'bbox_y_end': self.bbox_y_end
        }


class TrainingRun(db.Model):
    __tablename__ = 'training_runs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    num_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    loss: Mapped[float] = mapped_column(Float, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'model_version': self.model_version,
            'num_samples': self.num_samples,
            'accuracy': self.accuracy,
            'loss': self.loss,
            'trained_at': self.trained_at.isoformat() if self.trained_at else None
        }


class BatchJob(db.Model):
    __tablename__ = 'batch_jobs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(50), default='pending')
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_pages: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    results: Mapped[List["BatchResult"]] = relationship("BatchResult", back_populates="batch_job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'total_pages': self.total_pages,
            'processed_pages': self.processed_pages,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BatchResult(db.Model):
    __tablename__ = 'batch_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_job_id: Mapped[int] = mapped_column(Integer, ForeignKey('batch_jobs.id'), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey('documents.id'), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    batch_job: Mapped["BatchJob"] = relationship("BatchJob", back_populates="results")
    document: Mapped["Document"] = relationship("Document", back_populates="batch_results")

    def to_dict(self):
        return {
            'id': self.id,
            'batch_job_id': self.batch_job_id,
            'document_id': self.document_id,
            'extracted_text': self.extracted_text,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
