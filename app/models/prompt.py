from datetime import datetime
import json
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from app import db

# 标签和提示词的多对多关系表
tags_prompts = db.Table('tags_prompts',
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('prompt_id', db.Integer, db.ForeignKey('prompts.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(50), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Prompt(db.Model):
    __tablename__ = 'prompts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(100), index=True)
    content: Mapped[str] = mapped_column(db.Text)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    cover_image: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)  # 存储图片路径
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'))
    is_public: Mapped[bool] = mapped_column(db.Boolean, default=False)
    view_count: Mapped[int] = mapped_column(db.Integer, default=0)
    share_count: Mapped[int] = mapped_column(db.Integer, default=0)
    _metadata: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    
    # 多对多关系
    tags = relationship('Tag', secondary=tags_prompts, 
                      backref=db.backref('prompts', lazy='dynamic'), 
                      lazy='dynamic')
    
    @property
    def metadata(self):
        if self._metadata:
            return json.loads(self._metadata)
        return {}
    
    @metadata.setter
    def metadata(self, data):
        self._metadata = json.dumps(data)
    
    def add_tag(self, tag_name):
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        if tag not in self.tags.all():
            self.tags.append(tag)
    
    def remove_tag(self, tag_name):
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag and tag in self.tags.all():
            self.tags.remove(tag)
    
    def increment_view(self):
        self.view_count += 1
    
    def increment_share(self):
        self.share_count += 1
    
    def __repr__(self):
        return f'<Prompt {self.title}>' 