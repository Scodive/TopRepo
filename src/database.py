#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 创建数据库引擎
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///toprepo.db")
engine = create_engine(DATABASE_URL)

# 创建基类
Base = declarative_base()

class Repository(Base):
    """仓库模型"""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True)
    name = Column(String(100))
    full_name = Column(String(200), unique=True)
    owner = Column(String(100))
    owner_avatar = Column(String(255))
    description = Column(Text)
    url = Column(String(255))
    stars = Column(Integer)
    forks = Column(Integer)
    language = Column(String(50))
    created_at = Column(String(50))
    updated_at = Column(String(50))
    category = Column(String(20))  # 'new' or 'growing'
    growth_rate = Column(Float, nullable=True)
    stars_increased = Column(Integer, nullable=True)
    fetch_date = Column(String(20))
    timestamp = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            "id": self.github_id,
            "name": self.name,
            "full_name": self.full_name,
            "owner": self.owner,
            "owner_avatar": self.owner_avatar,
            "description": self.description,
            "url": self.url,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "category": self.category,
            "growth_rate": self.growth_rate,
            "stars_increased": self.stars_increased,
            "fetch_date": self.fetch_date
        }

class Subscriber(Base):
    """订阅者模型"""
    __tablename__ = "subscribers"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    name = Column(String(100), nullable=True)
    subscribed_at = Column(DateTime, default=datetime.now)
    is_active = Column(Integer, default=1)  # 1: active, 0: inactive
    token = Column(String(100), unique=True)  # 用于退订
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "subscribed_at": self.subscribed_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": self.is_active == 1
        }

# 创建表
Base.metadata.create_all(engine)

# 创建会话
Session = sessionmaker(bind=engine)

class Database:
    def __init__(self):
        self.session = Session()
    
    def save_repos(self, repos):
        """保存仓库数据到数据库"""
        try:
            for repo_data in repos:
                # 检查是否已存在
                existing_repo = self.session.query(Repository).filter_by(github_id=repo_data["id"]).first()
                
                if existing_repo:
                    # 更新现有记录
                    existing_repo.stars = repo_data["stars"]
                    existing_repo.forks = repo_data["forks"]
                    existing_repo.description = repo_data["description"]
                    existing_repo.updated_at = repo_data["updated_at"]
                    existing_repo.category = repo_data["category"]
                    existing_repo.fetch_date = repo_data["fetch_date"]
                    
                    if "growth_rate" in repo_data:
                        existing_repo.growth_rate = repo_data["growth_rate"]
                    
                    if "stars_increased" in repo_data:
                        existing_repo.stars_increased = repo_data["stars_increased"]
                else:
                    # 创建新记录
                    new_repo = Repository(
                        github_id=repo_data["id"],
                        name=repo_data["name"],
                        full_name=repo_data["full_name"],
                        owner=repo_data["owner"],
                        owner_avatar=repo_data["owner_avatar"],
                        description=repo_data["description"],
                        url=repo_data["url"],
                        stars=repo_data["stars"],
                        forks=repo_data["forks"],
                        language=repo_data["language"],
                        created_at=repo_data["created_at"],
                        updated_at=repo_data["updated_at"],
                        category=repo_data["category"],
                        fetch_date=repo_data["fetch_date"]
                    )
                    
                    if "growth_rate" in repo_data:
                        new_repo.growth_rate = repo_data["growth_rate"]
                    
                    if "stars_increased" in repo_data:
                        new_repo.stars_increased = repo_data["stars_increased"]
                    
                    self.session.add(new_repo)
            
            self.session.commit()
            logger.info(f"成功保存 {len(repos)} 个仓库到数据库")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"保存仓库数据时出错: {str(e)}")
            return False
    
    def get_trending_repos(self, category="new", limit=20):
        """获取trending仓库"""
        try:
            repos = self.session.query(Repository).filter_by(category=category).order_by(
                Repository.fetch_date.desc(), 
                Repository.stars.desc()
            ).limit(limit).all()
            
            return [repo.to_dict() for repo in repos]
        except Exception as e:
            logger.error(f"获取trending仓库时出错: {str(e)}")
            return []
    
    def get_growing_repos(self, limit=20):
        """获取增长最快的仓库"""
        try:
            repos = self.session.query(Repository).filter_by(category="growing").order_by(
                Repository.fetch_date.desc(), 
                Repository.growth_rate.desc()
            ).limit(limit).all()
            
            return [repo.to_dict() for repo in repos]
        except Exception as e:
            logger.error(f"获取增长最快的仓库时出错: {str(e)}")
            return []
    
    def add_subscriber(self, email, name=None, token=None):
        """添加订阅者"""
        try:
            # 检查是否已存在
            existing_sub = self.session.query(Subscriber).filter_by(email=email).first()
            
            if existing_sub:
                if existing_sub.is_active == 0:
                    # 重新激活
                    existing_sub.is_active = 1
                    existing_sub.subscribed_at = datetime.now()
                    self.session.commit()
                    logger.info(f"重新激活订阅者: {email}")
                    return True
                else:
                    logger.info(f"订阅者已存在: {email}")
                    return False
            else:
                # 创建新订阅者
                new_sub = Subscriber(
                    email=email,
                    name=name,
                    token=token
                )
                self.session.add(new_sub)
                self.session.commit()
                logger.info(f"添加新订阅者: {email}")
                return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"添加订阅者时出错: {str(e)}")
            return False
    
    def remove_subscriber(self, email=None, token=None):
        """移除订阅者"""
        try:
            if email:
                sub = self.session.query(Subscriber).filter_by(email=email).first()
            elif token:
                sub = self.session.query(Subscriber).filter_by(token=token).first()
            else:
                return False
            
            if sub:
                sub.is_active = 0
                self.session.commit()
                logger.info(f"移除订阅者: {sub.email}")
                return True
            else:
                logger.info("未找到订阅者")
                return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"移除订阅者时出错: {str(e)}")
            return False
    
    def get_active_subscribers(self):
        """获取所有活跃订阅者"""
        try:
            subs = self.session.query(Subscriber).filter_by(is_active=1).all()
            return [sub.to_dict() for sub in subs]
        except Exception as e:
            logger.error(f"获取订阅者时出错: {str(e)}")
            return []
    
    def close(self):
        """关闭会话"""
        self.session.close() 