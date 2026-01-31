from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PeriodColumn(Base):
    __tablename__ = "period_columns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Период")
    order = Column(Integer, default=0)
    
    cells = relationship("Cell", back_populates="period", cascade="all, delete-orphan", lazy="selectin")

class Row(Base):
    __tablename__ = "rows"
    
    id = Column(Integer, primary_key=True, index=True)
    order = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("rows.id", ondelete="CASCADE"), nullable=True)
    level = Column(Integer, default=0)
    entity = Column(String, default="")
    article = Column(String, default="")
    project = Column(String, default="")
    
    # Self-referential: только один cascade - на children
    children = relationship(
        "Row", 
        back_populates="parent",
        remote_side=[id],
        cascade="all, delete-orphan",
        single_parent=True,  # Важно для self-referential
        lazy="selectin"
    )
    parent = relationship("Row", back_populates="children", remote_side=[parent_id])
    cells = relationship("Cell", back_populates="row", cascade="all, delete-orphan", lazy="selectin")

class Cell(Base):
    __tablename__ = "cells"
    
    id = Column(Integer, primary_key=True, index=True)
    row_id = Column(Integer, ForeignKey("rows.id", ondelete="CASCADE"))
    period_id = Column(Integer, ForeignKey("period_columns.id", ondelete="CASCADE"))
    value = Column(Float, nullable=True)
    
    row = relationship("Row", back_populates="cells")
    period = relationship("PeriodColumn", back_populates="cells")
