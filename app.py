import pymysql
import json
import sys

from flask import Flask, jsonify, request, flash, render_template,redirect,url_for,make_response
from sqlalchemy import create_engine
from passlib.hash import bcrypt
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from sqlalchemy.orm import Session,sessionmaker


from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
from convert_to_json import *
import configparser





app=Flask(__name__)

path="test.ini"
config = configparser.ConfigParser()
config.read(path)

app.config["JWT_COOKIE_SECURE"] = config['SECURITY'].getboolean("JWT_COOKIE_SECURE",False)
app.config["JWT_SECRET_KEY"] = config['SECURITY'].get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=config['SECURITY'].getint("JWT_ACCESS_TOKEN_EXPIRES",1))
app.config["JWT_COOKIE_CSRF_PROTECT"] = config['SECURITY'].getboolean("JWT_COOKIE_CSRF_PROTECT",False)

jwt = JWTManager(app)

engine = create_engine(config['DATABASE'].get("Connection_string"),echo = True)
Session = sessionmaker()
session = Session(bind=engine)

from models import User,Notification,Subscription

@jwt.unauthorized_loader
def custom_unauthorized_response(_err):
    return jsonify({'message':"Необходимо авторизоваться"})


@app.route('/login',methods=['POST'])
def login():
    session = Session(bind=engine)
    request_data = request.get_json()

    nickname = request_data['nickname']
    password = request_data['password']
    user = session.query(User).filter(User.nickname == nickname).first()
    session.close()
    if not user or not bcrypt.verify(password,user.password):
        return jsonify({"data":False,
                     "message":"Неправильный логин/пароль"
                     })
    access_token = create_access_token(identity=user.id_user)
    return jsonify({"data":True,
                 "message":"Вход успешно выполнен",
                 "access_token":access_token
                 })

@app.route('/register',methods=['POST'])
def register():
    session = Session(bind=engine)
    request_data = request.get_json()

    nickname = request_data['nickname']
    password = request_data['password']

    user=session.query(User).filter(User.nickname==nickname).first()
    session.close()
    if user:
        return jsonify({"data":False,
                     "message":"Этот никнейм уже занят"
                     })
    session = Session(bind=engine)
    user=User(nickname=nickname, password=password)
    session.add(user)
    session.commit()
    session.close()
    return jsonify({
        "data":True,
        "message":"Регистрация выполнена успешно"
    })

@app.route('/subscribe',methods=['POST'])
@jwt_required()
def subscribe():
    id_user = get_jwt_identity()
    if id_user:
        result = subscribe_DB(id_user)
        return jsonify({'data':result,
                        'message':"Подписка успешно оформлена" if result else "Ошибка"})
    return jsonify({'error':'Missing data'})

@app.route('/unsubscribe',methods=['POST'])
@jwt_required()
def unsubscribe():
    id_user = get_jwt_identity()
    if id_user:
        result = unsubscribe_DB(id_user)
        return jsonify({'data':result,
                        'message':"Подписка успешно отменена" if result else "Ошибка"})
    return jsonify({'error':'Missing data'})

@app.route('/send_notification',methods=['POST'])
@jwt_required()
def send_notifications():
    request_data = request.get_json()

    id_subscriber = request_data['id_subscriber']
    if id_subscriber:
        header = request_data['header']
        text = request_data['text']
        result = send_notification_DB(header, text, id_subscriber)
        return jsonify({'data':result,
                        'message':"Уведомление успешно отправлено" if result else "Ошибка"})
    return jsonify({'error':'Missing data'})

@app.route('/notifications',methods=['GET'])
@jwt_required()
def get_notifications():
    id_subscriber = get_jwt_identity()
    notifications = get_notifications_DB(id_subscriber)
    return jsonify({'data': notifications,
                    'message': "Уведомления получены" if notifications!=None else "Вы не подписаны на уведомления"})





#SQL'ка
def subscribe_DB(id_user):
    session = Session(bind=engine)
    result=True
    try:
        subscription = session.query(Subscription).filter(Subscription.id_subscriber==id_user).first()
        if not subscription:
            new_subscription = Subscription(id_subscriber=id_user)
            session.add(new_subscription)
            session.commit()
    except:
        session.rollback()
        print('rolled back')
        result = False
        raise
    finally:
        session.close()
        return result

def unsubscribe_DB(id_user):
    session = Session(bind=engine)
    result = True
    try:
        subscription = session.query(Subscription).filter(Subscription.id_subscriber==id_user).first()
        session.delete(subscription)
        session.commit()
    except:
        session.rollback()
        print('rolled back')
        result = False
        raise
    finally:
        session.close()
        return result

def send_notification_DB(header,text,id_subscriber):
    session = Session(bind=engine)
    result = True
    try:
        new_notification = Notification(header=header,text=text,id_recipient=id_subscriber)
        session.add(new_notification)
        session.commit()
    except:
        session.rollback()
        print('rolled back')
        result = False
        raise
    finally:
        session.close()
        return result

def get_notifications_DB(id_subscriber):
    session = Session(bind=engine)
    try:
        if not session.query(Subscription).filter(Subscription.id_subscriber == id_subscriber):
            Notifications = None
        else:
            Notifications = notifications_to_json(session.query(Notification).filter(Notification.id_recipient==id_subscriber).all())
    except:
        session.rollback()
        print('rolled back')
        Notifications = None
        raise
    finally:
        session.close()
        return Notifications

if __name__ == '__main__':
    app.run(debug=True,use_reloader=False, host="0.0.0.0")

