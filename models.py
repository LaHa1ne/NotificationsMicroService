import enum

import sqlalchemy as db
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from passlib.hash import bcrypt
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
     __tablename__='users'
     id_user=db.Column(db.Integer,primary_key=True)
     nickname=db.Column(db.String(15),nullable=False)
     password = db.Column(db.String(250), nullable=False)
     notification=relationship('Notification',backref='users')
     subscriber = relationship('Subscription', backref='users')

     def __init__(self,**kwargs):
         self.nickname=kwargs.get('nickname')
         self.password=bcrypt.hash(kwargs.get('password'))

class Notification(Base):
    __tablename__='notifications'
    id_notification=db.Column(db.Integer,primary_key=True)
    header = db.Column(db.String(15), nullable=False)
    text = db.Column(db.String(45), nullable=False)
    id_recipient=db.Column(db.Integer, db.ForeignKey('users.id_user'), nullable=False)

class Subscription(Base):
    __tablename__='subscriptions'
    id_subscription=db.Column(db.Integer,primary_key=True)
    id_subscriber=db.Column(db.Integer,db.ForeignKey('users.id_user'), nullable=False)

