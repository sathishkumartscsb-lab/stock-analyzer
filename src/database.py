from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from src.config import DB_PATH
import os

Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    name = Column(String)
    sector = Column(String)
    
    fundamentals = relationship("Fundamental", back_populates="stock")
    technicals = relationship("Technical", back_populates="stock")
    news_trends = relationship("NewsTrend", back_populates="stock")
    scores = relationship("Score", back_populates="stock", uselist=False)
    reports = relationship("Report", back_populates="stock")

class Fundamental(Base):
    __tablename__ = 'fundamentals'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    param_code = Column(String)
    value = Column(Float)
    score = Column(Float) # 0, 0.5, 1
    status = Column(String) # Positive/Neutral/Negative
    
    stock = relationship("Stock", back_populates="fundamentals")

class Technical(Base):
    __tablename__ = 'technicals'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    param_code = Column(String)
    value = Column(Float)
    score = Column(Float)
    status = Column(String)
    
    stock = relationship("Stock", back_populates="technicals")

class NewsTrend(Base):
    __tablename__ = 'news_trends'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    param_code = Column(String)
    value = Column(Float) # Could be 1/0 for boolean flags or count
    score = Column(Float)
    status = Column(String)
    
    stock = relationship("Stock", back_populates="news_trends")

class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    fundamental_score = Column(Float)
    technical_score = Column(Float)
    news_score = Column(Float)
    total_score = Column(Float)
    health_label = Column(String) # Buy/Hold/Avoid
    
    stock = relationship("Stock", back_populates="scores")

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    image_path = Column(String)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock", back_populates="reports")

def init_db():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    return Session()
