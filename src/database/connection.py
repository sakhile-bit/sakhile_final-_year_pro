"""
Database Connection and Management Module
Handles MySQL database operations for the assessment tool
"""

import os
from contextlib import contextmanager
from typing import Optional, Any, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime

from ..utils.logging_config import get_logger
from ..utils.config import config

logger = get_logger(__name__)

# Create base class for models
Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='assessor')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessments = relationship("Assessment", back_populates="assessor")


class Business(Base):
    """Business model"""
    __tablename__ = 'businesses'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(50), unique=True)
    address = Column(Text)
    contact_person = Column(String(100))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    industry = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assessments = relationship("Assessment", back_populates="business")


class Assessment(Base):
    """Assessment model"""
    __tablename__ = 'assessments'

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    assessor_id = Column(Integer, ForeignKey('users.id'))
    assessment_date = Column(DateTime, default=datetime.utcnow)
    system_info = Column(JSON)
    controls_results = Column(JSON, nullable=False)
    total_score = Column(Integer, nullable=False)
    certification_level = Column(String(20), nullable=False)
    recommendations = Column(JSON)
    status = Column(String(20), default='completed')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business = relationship("Business", back_populates="assessments")
    assessor = relationship("User", back_populates="assessments")
    certificates = relationship("Certificate", back_populates="assessment")


class Certificate(Base):
    """Certificate model"""
    __tablename__ = 'certificates'

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'), nullable=False)
    certificate_number = Column(String(50), unique=True, nullable=False)
    issued_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    certificate_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="certificates")


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class DatabaseManager:
    """
    Database connection and session management
    """

    def __init__(self):
        """Initialize database connection"""
        self.engine = None
        self.SessionLocal = None
        self._connect()

    def _connect(self):
        """Create database connection using the centralized config URL."""
        try:
            connection_url = config.get_database_url()

            # Create engine
            self.engine = create_engine(
                connection_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=config.app.get('debug', False)
            )

            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            logger.info("Database connection established successfully")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Get database session with automatic cleanup

        Yields:
            Session: Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def init_database(self):
        """Initialize database schema"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def save_assessment(self, results, business_info, assessor_id=None):
        """
        Save assessment results to database

        Args:
            results: AssessmentResult object
            business_info: BusinessInfo object
            assessor_id: ID of the assessor (optional)
        """
        with self.get_session() as session:
            # Check if business exists, create if not
            business = session.query(Business).filter_by(
                registration_number=business_info.id
            ).first()

            if not business:
                business = Business(
                    name=business_info.name,
                    registration_number=business_info.id,
                    address=business_info.address,
                    contact_person=business_info.contact_person,
                    contact_email=business_info.contact_email,
                    contact_phone=business_info.contact_phone,
                    industry=business_info.industry
                )
                session.add(business)
                session.flush()  # Get the ID

            # Prepare controls results for JSON storage
            controls_data = {
                control_id: {
                    "name": control.name,
                    "score": control.score,
                    "weight": control.weight,
                    "status": control.status,
                    "details": control.details
                }
                for control_id, control in results.controls.items()
            }

            # Create assessment record
            assessment = Assessment(
                business_id=business.id,
                assessor_id=assessor_id,
                assessment_date=results.assessment_date,
                system_info=getattr(results, 'system_info', None),
                controls_results=controls_data,
                total_score=results.score,
                certification_level=results.certification_level,
                recommendations=results.recommendations,
                status='completed'
            )

            session.add(assessment)
            session.flush()

            logger.info(f"Assessment saved to database with ID: {assessment.id}")
            return assessment.id

    def get_assessment_stats(self):
        """
        Get assessment statistics

        Returns:
            Dict with statistics
        """
        with self.get_session() as session:
            total = session.query(Assessment).count()
            gold = session.query(Assessment).filter_by(certification_level='GOLD').count()
            silver = session.query(Assessment).filter_by(certification_level='SILVER').count()
            bronze = session.query(Assessment).filter_by(certification_level='BRONZE').count()
            not_certified = session.query(Assessment).filter_by(certification_level='NOT_CERTIFIED').count()

            return {
                'total': total,
                'gold': gold,
                'silver': silver,
                'bronze': bronze,
                'not_certified': not_certified
            }

    def get_recent_assessments(self, limit=10):
        """
        Get recent assessments

        Args:
            limit: Maximum number of assessments to return

        Returns:
            List of assessment records
        """
        with self.get_session() as session:
            return session.query(Assessment).order_by(Assessment.created_at.desc()).limit(limit).all()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
