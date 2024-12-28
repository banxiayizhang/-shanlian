from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets
from flask_cors import CORS
import numpy as np
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime
import uuid
#加多
import os
from sqlalchemy import or_, text,func
from sqlalchemy.orm import joinedload
from functools import wraps
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
from urllib.parse import quote_plus
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy import Column, String, Text, TIMESTAMP
import logging

app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(16)
password = quote_plus('@Zx2022611039')
password = quote_plus('@Zx2022611039')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/mydata'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#登录注册使用的user表格
class User(db.Model):
    __tablename__ = 'users'
    #id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone_number = db.Column(db.String(15), unique=True, nullable=False) 
    #username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    user_info = db.relationship('UserInfo', back_populates='user', uselist=False,lazy=True, foreign_keys='UserInfo.id')

    
class UserInfo(db.Model):
    _tablename_ = 'user_info'
    
    id = db.Column(db.String(36),db.ForeignKey('users.id'),primary_key = True)
    username = db.Column(db.String(50),nullable = False)
    gender = db.Column(db.String(10), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    college = db.Column(db.String(20),nullable=False)
    signature = db.Column(db.Text , nullable = True)
    hometown = db.Column(db.String(255) ,nullable = True)
    hobby = db.Column(db.String(255) ,nullable = True)
    campus = db.Column(db.String(255) ,nullable = False)
    major = db.Column(db.String(255) ,nullable = True)
    constellation = db.Column(db.String(50) , nullable = True)
    mbti = db.Column(db.String(50) , nullable = True)
    declaration = db.Column(db.Text ,nullable = True)
    personality = db.Column(db.String(255) ,nullable = True)
    avatar = db.Column(db.String(255) , nullable = True)
    birthday = db.Column(db.String(255) , nullable = True)
    user = db.relationship('User', back_populates='user_info',lazy=True, foreign_keys=[id])
    def to_dict(self):
        return {
            'username': self.username,
            'gender': self.gender,
            'campus': self.campus,
            'college': self.college,
            'grade': self.grade,
            'id': self.id
        } 

    
#聊天界面使用的好友关系表格    
class Friend(db.Model):
    __tablename__ = 'friends'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)#表示第几条信息
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # 确保 user_id 和 friend_id 不相同
    __table_args__ = (
        db.UniqueConstraint('user_id', 'friend_id', name='uq_user_friend'),
    )

    def __init__(self, user_id, friend_id):
        if user_id == friend_id:
            raise ValueError("user_id and friend_id cannot be the same")
        self.user_id = user_id
        self.friend_id = friend_id

#已聊对象的表格
class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    chat_partner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    last_message_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())  # 最后消息时间

    # 确保 user_id 和 chat_partner_id 不相同
    __table_args__ = (
        db.UniqueConstraint('user_id', 'chat_partner_id', name='uq_user_chat_partner'),
    )

    def __init__(self, user_id, chat_partner_id):
        if user_id == chat_partner_id:
            raise ValueError("user_id and chat_partner_id cannot be the same")
        self.user_id = user_id
        self.chat_partner_id = chat_partner_id
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __repr__(self):
        return f"<Message from {self.sender_id} to {self.receiver_id} at {self.timestamp}>"

#论坛表格
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    photo = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.String(36), db.ForeignKey('user_info.id'))
    author = db.relationship('UserInfo', backref=db.backref('questions'))


class Answer(db.Model):
    __tablename__ = 'answer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    author_id = db.Column(db.String(36), db.ForeignKey('user_info.id'))
    question = db.relationship('Question', backref=db.backref('answers', order_by=id.desc()))
    author = db.relationship('UserInfo', backref=db.backref('answers'))
    
class BlindBoxEntry(db.Model):
    __tablename__ = 'blind_box_entry'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user_info.id'), nullable=False)
    gender = db.Column(db.String(36),nullable = False)
    content = db.Column(db.Text, nullable=False)  # 纸条内容
    wechat_id = db.Column(db.String(100))  # 仅抽取者可见
    score = db.Column(db.Integer, default=0)  # 纸条分数
    count = db.Column(db.Integer)

    user = db.relationship('UserInfo', backref=db.backref('entries', lazy=True)) 


#自动生成表格    
with app.app_context():
    db.create_all() 
#随机生成 id    
def generate_random_id():
    return str(uuid.uuid4())  # 生成 36 位随机 UUID
#-----------------------------------------------------改👇
def add_chat_relationship(sender_id, receiver_id):
    # 检查是否已经存在相同的聊天关系
    existing_relationship = ChatRelationship.query.filter_by(sender_id=sender_id, receiver_id=receiver_id).first()
    
    if not existing_relationship:
        # 创建新的聊天关系
        new_relationship = ChatRelationship(sender_id=sender_id, receiver_id=receiver_id)
        db.session.add(new_relationship)
        db.session.commit()
        print(f"Chat relationship added: {sender_id} -> {receiver_id}")
    else:
        print(f"Chat relationship already exists: {sender_id} -> {receiver_id}")
#-----------------------------------------------------改👆

#main页面指的是登录、注册一开始出现的页面
@app.route('/')
def home():
    return render_template('main.html')
#注册界面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #username = request.form['username']
        phone_number = request.form['phone_number']
        password = request.form['psw']
        confirm_password = request.form['confirm_psw']
        name = request.form['name']
        email = request.form['email']

        # 密码确认
        if password != confirm_password:
            flash('密码不匹配，请重试。', 'danger')
            return redirect(url_for('register'))

        # 检查用户名是否已存在（防止重复注册）
        existing_user = User.query.filter_by(phone_number = phone_number).first()
        if existing_user:
            flash('该号码已被注册', 'danger')
            return redirect(url_for('register'))

        # 插入用户数据
        try:
            id = generate_random_id()
            hashed_password = generate_password_hash(password)  # 哈希密码
            new_user = User(id = id , phone_number = phone_number, password=hashed_password, name=name, email=email)
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功！', 'success')
            return redirect(url_for('login'))  # 注册成功后重定向到登录页面
        except Exception as e:
            db.session.rollback()  # 如果出错，回滚
            print(e)  # 打印错误信息
            flash('注册失败，请重试。', 'danger')

    return render_template('register.html')

# 注册成功页面
@app.route('/success')
def success():
    return "注册成功！"

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        password = request.form['psw']

        # 查询数据库以验证用户
        user = User.query.filter_by(phone_number = phone_number).first()  # 查找用户

        if user and check_password_hash(user.password, password):  # 验证密码
            session['user_id'] = user.id  # 将用户 ID 存储在会话中
            flash('登录成功！', 'success')
            return redirect(url_for('main_page'))  # 登录成功后重定向到主页
        else:
            flash('手机号或密码错误！', 'danger')

    return render_template('login.html')

#忘记密码
@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    phone_number = data.get('phone_number')
    new_password = data.get('new_password')

    if not phone_number or not new_password:
        return jsonify({'success': False, 'message': '缺少必要的参数'}), 400

    # 查询用户是否存在
    user = User.query.filter_by(phone_number=phone_number).first()

    if not user:
        return jsonify({'success': False, 'message': '手机号不存在'}), 404

    try:
        # 更新密码
        user.password = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': '密码重置成功！'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

#首页
@app.route('/main_page', methods=['GET', 'POST'])
#@login_required
def main_page():
    current_user_id = session.get('user_id')

    if current_user_id is None:
        return redirect(url_for('login'))

    user_info = UserInfo.query.filter_by(id=current_user_id).first()
    username = user_info.username if user_info else None
    if not user_info:
        return redirect(url_for('index',username=username))
    if request.method == 'POST':
        pass
    
    return redirect(url_for('index',username=username))


@app.route('/index')
def index():
    current_user_id = session.get('user_id')
    
    if current_user_id is None:
        return redirect(url_for('login'))

    user_info = UserInfo.query.filter_by(id=current_user_id).first()
    username = user_info.username if user_info else None
    questions = Question.query.options(joinedload(Question.author)).order_by(Question.create_time.desc()).all()
    #user_info_missing = request.args.get('user_info_missing', False, type=bool) 
    top_questions = db.session.query(
    Question, 
    func.count(Answer.id).label('answer_count')
).join(Answer, Answer.question_id == Question.id) \
 .group_by(Question.id) \
 .order_by(func.count(Answer.id).desc()) \
 .limit(10) \
 .all()
    if not user_info:
        user_info_missing = True
    else:
        user_info_missing = False
    context = {
        'questions': questions,
        'top_questions': top_questions#热度最高的前十个话题
    }
    return render_template('index.html', username=username, **context,user_info_missing=user_info_missing)


    
# 个人中心路由
@app.route('/personal')
def personal():
    current_user_id = session.get('user_id')
    
    return render_template('personal.html',user_id = current_user_id)

@app.route('/update_info', methods=['POST'])
def update_info():
    if request.method == 'POST':
        try:
            #判断当前用户是否登录
            current_user_id = session.get('user_id')
            if not current_user_id:
                return redirect(url_for('login'))
            
            #获取 Json 数据
            data = request.get_json()
            
            print(f"接收到的数据: {data}")
            
            username = data.get('username')
            gender = data.get('gender')
            grade = data.get('grade')
            college = data.get('college')
            signature = data.get('signature')
            hometown = data.get('hometown')
            hobby = data.get('hobby')
            campus = data.get('campus')
            major = data.get('major')
            constellation = data.get('constellation')
            mbti = data.get('mbti')
            declaration = data.get('declaration')
            personality = data.get('personality')
            avatar = data.get('avatar')  # 头像URL
            birthday = data.get('birthday')

            # 检查是否有缺少必要参数
            if not all([username, gender, grade,campus,college]):
                return jsonify({'message': '缺少必要参数'}), 400

            # 查询用户是否存在
            user = UserInfo.query.filter_by(id=current_user_id).first()

            if user:
                # 如果用户存在，更新用户信息
                user.username = username
                user.gender = gender
                user.grade = grade
                user.college = college
                user.signature = signature
                user.hometown = hometown
                user.hobby = hobby
                user.campus = campus
                user.major = major
                user.constellation = constellation
                user.mbti = mbti
                user.declaration = declaration
                user.personality = personality
                user.avatar = avatar
                user.birthday = birthday
                db.session.commit()
                return jsonify({'message': '信息更新成功！'}), 200
            else:
                # 如果用户不存在，插入新记录
                new_user = UserInfo(
                    id=current_user_id,
                    username=username,
                    gender=gender,
                    grade=grade,
                    college = college,
                    signature=signature,
                    hometown=hometown,
                    hobby=hobby,
                    campus=campus,
                    major=major,
                    constellation=constellation,
                    mbti=mbti,
                    declaration=declaration,
                    personality=personality,
                    avatar=avatar,
                    birthday=birthday
                )
                db.session.add(new_user)
                db.session.commit()
                return jsonify({'message': '信息保存成功！'}), 200
        
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'message': '请求解析失败，请检查请求格式。'}), 400
    return jsonify({'message': '无效请求'}), 400


# 汕恋路由
@app.route('/shanlian')
def shanlian():
    return render_template('shanlian.html')


@app.route('/api/shanlian')
def api_shanlian():
    users = UserInfo.query.all()
    user_data = [user.to_dict() for user in users]  # 转换为字典格式
    return jsonify(user_data)


@app.route('/filter_users')
def filter_users():
    filters = request.args.to_dict()

    query = UserInfo.query

    # 处理多个筛选条件
    for key, value in filters.items():
        if value != 'all':
            query = query.filter(getattr(UserInfo, key) == value)

    users = query.all()
    return [user.to_dict() for user in users]

@app.route('/add_to_chat', methods=['POST'])
def add_to_chat():
    try:
        data = request.get_json()
        print("Received data:", data)  # 输出接收到的请求数据
        
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')

        # 检查 ID 是否有效
        if not sender_id or not receiver_id:
            return jsonify({"status": "error", "message": "缺少 sender_id 或 receiver_id"}), 400

        # 添加聊天关系
        new_chat_relationship = Friend(user_id=sender_id, friend_id=receiver_id)
        db.session.add(new_chat_relationship)
        db.session.commit()

        return jsonify({"status": "success", "message": "成功添加到对话列表"})

    except Exception as e:
        print("Error:", str(e))  # 输出错误信息用于调试
        return jsonify({"status": "error", "message": "服务器错误"}), 500
    
@app.route('/get_chat_relationships', methods=['GET'])
def get_chat_relationships():
    try:
        user_id = session.get('user_id')  # 假设用户 ID 存储在 session 中
        
        if not user_id:
            return jsonify({"status": "error", "message": "用户未登录"}), 400

        # 获取所有与当前用户有聊天关系的用户
        chatted_users = db.session.query(User).join(ChatRelationship, 
            (ChatRelationship.sender_id == User.id) | (ChatRelationship.receiver_id == User.id))\
            .filter((ChatRelationship.sender_id == user_id) | (ChatRelationship.receiver_id == user_id))\
            .all()

        users_data = [{"id": user.id, "username": user.username} for user in chatted_users]

        return jsonify({"status": "success", "chatted_users": users_data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/chat')
def chat():
    """聊天功能"""
    if 'user_id' not in session:
        flash("请先登录", 'error')
        return redirect(url_for('login'))

    # 获取当前用户的好友列表
    friends = db.session.query(UserInfo).join(Friend, Friend.friend_id == UserInfo.id).filter(Friend.user_id == session['user_id']).all()

    # 获取与某个好友的聊天记录
    receiver_id = request.args.get('receiver_id')  # 从 URL 参数中获取 receiver_id
    messages = []
    receiver_username = ''
    if receiver_id:
        # 查找目标好友的用户名
        receiver = User.query.get(receiver_id)
        if receiver:
            receiver_username = receiver.user_info.username

        # 查询与该好友的聊天记录
        messages = Message.query.filter(
            ((Message.sender_id == session['user_id']) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == session['user_id']))
        ).order_by(Message.timestamp).all()

    return render_template('chat.html', friends=friends, messages=messages, receiver_id=receiver_id, receiver_username=receiver_username)

@app.route('/add_friend', methods=['POST'])
def add_friend():
    """通过手机号添加好友"""
    # 确保当前用户已登录
    current_user_id = session['user_id']

    # 获取请求体中的手机号
    phone_number = request.json.get('phone_number')  # 获取 json 请求体
    if not phone_number:
        return jsonify({'error': '手机号不能为空'}), 400

    # 查找目标用户（通过手机号查找，不需要检查对方是否登录）
    friend = User.query.filter_by(phone_number=phone_number).first()
    if not friend:
        return jsonify({'error': '手机号对应的用户不存在'}), 404

    # 检查是否是当前用户
    if friend.id == current_user_id:
        return jsonify({'error': '不能添加自己为好友'}), 400

    # 检查是否已经是好友
    existing_friendship = Friend.query.filter_by(user_id=current_user_id, friend_id=friend.id).first()
    if existing_friendship:
        return jsonify({'status': 'error', 'message': '已经是好友'}), 400

    # 添加好友关系
    new_friend = Friend(user_id=current_user_id, friend_id=friend.id)
    db.session.add(new_friend)
    db.session.commit()

    # 获取当前用户的好友列表
    friends = User.query.join(Friend, Friend.friend_id == User.id).filter(Friend.user_id == current_user_id).all()

    # 返回好友列表
    return jsonify({
        'status': 'success',
        'friends': [{
            'id': friend.id,
            'username': friend.user_info.username,
            'avatar': friend.user_info.avatar  # 你可以返回更多的字段（如 friend.id 等）
        } for friend in friends]
    })

@app.route('/send_message', methods=['POST'])
def send_message():
    """发送消息"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    data = request.get_json()
    receiver_id = data.get('receiver_id')
    message_content = data.get('message')

    if not receiver_id or not message_content:
        return jsonify({'status': 'error', 'message': '缺少必要的参数'}), 400

    # 验证接收者 ID 是否存在
    receiver = User.query.filter_by(id=receiver_id).first()
    if not receiver:
        return jsonify({'status': 'error', 'message': '接收者不存在'}), 400

    try:
        new_message = Message(sender_id=session['user_id'], receiver_id=receiver_id, content=message_content)
        db.session.add(new_message)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': '消息发送成功',
            'message_data': {
                'sender_id': new_message.sender_id,
                'receiver_id': new_message.receiver_id,
                'message': new_message.content,
                'timestamp': new_message.timestamp.isoformat()
            }
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取当前用户信息
@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    # 检查用户是否已登录
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    # 获取当前用户的 user_id
    user_id = session['user_id']
    
    # 查找用户在数据库中的信息
    user = User.query.get(user_id)  # 获取 User 表中的记录
    
    if user:
        # 获取与用户相关的详细信息（例如 UserInfo）
        user_info = user.user_info  # 这里通过关系获取 UserInfo 信息
        if user_info:
            return jsonify({
                'user_id': user.id,
                'username': user_info.username,
                'gender': user_info.gender,
                'college': user_info.college,
                'grade': user_info.grade,
                'campus': user_info.campus
            }), 200
        else:
            return jsonify({'error': '用户信息未找到'}), 404
    else:
        return jsonify({'error': '用户不存在'}), 404

@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': '请先登录'}), 401

        receiver_id = request.args.get('receiver_id')  # 获取接收者的 ID
        if not receiver_id:
            return jsonify({'status': 'error', 'message': '缺少接收者 ID'}), 400

        # 查询聊天记录
        messages = Message.query.filter(
            ((Message.sender_id == session['user_id']) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == session['user_id']))
        ).order_by(Message.timestamp).all()

        # 将消息数据返回给前端
        message_data = [
            {
                'sender_id': message.sender_id,
                'receiver_id': message.receiver_id,
                'message': message.content,
                'timestamp': message.timestamp.isoformat()
            } for message in messages
        ]

        return jsonify({'status': 'success', 'messages': message_data})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

#论坛路由
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static\\uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
"""""
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function
"""
@app.route('/logout/')
def logout():
    # session.pop('user_id')
    # del session('user_id')
    session.clear()
    return redirect(url_for('login'))


@app.route('/question/', methods=['GET', 'POST'])
#@login_required
def question():
    if request.method == 'GET':
        return render_template('question.html')
    else:
        title = request.form.get('title')
        content = request.form.get('content')
        photo = request.files.get('photo')
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)  # Ensure a secure filename
            photo.save(os.path.join(UPLOAD_FOLDER, filename))  # Save the photo to the 'uploads' folder
            photo_url = url_for('static', filename=f'uploads/{filename}')  # URL to access the photo
        else:
            photo_url = None

        user_id = session.get('user_id')
        user = UserInfo.query.get(user_id)
        question = Question(title=title, content=content, author=user, photo=photo_url)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/detail/<int:question_id>/')
#@login_required
def detail(question_id):
    question_model = Question.query.get(question_id)
    return render_template('detail.html', question=question_model)

@app.route('/add_answer/', methods=['POST'])
#@login_required
def add_answer():
    content = request.form.get('answer_content')
    question_id = request.form.get('question_id')
    user_id = session.get('user_id')
    answer = Answer(content=content, question_id=question_id, author_id=user_id)
    db.session.add(answer)
    db.session.commit()
    return redirect(url_for('detail', question_id=question_id))


@app.context_processor
def inject_user_info():
    user_id = session.get('user_id')
    if user_id:
        user_info = UserInfo.query.filter_by(id=user_id).first()
        username = user_info.username if user_info else None
    else:
        username = None
    return {'username': username}

#纸条盲盒路由
@app.route('/blindbox',methods=['GET','POST'])
def blindbox():
    return render_template('blindbox.html')

@app.route('/update_scores', methods=['POST'])
def update_scores():
    # 遍历所有纸条，计算评论数量并更新评分
    entries_male = BlindBoxEntry.query.all()
    
    for entry in entries_male:
        score = (
            Question.query.filter_by(author_id=entry.user_id).count() + 
            Answer.query.filter_by(author_id=entry.user_id).count()+
            entry.count
        )  # 统计该纸条的评论数量和回答数量
        entry.score = score  # 更新评分
        db.session.commit()

    return jsonify({"message": "Scores updated successfully"}), 200


@app.route('/add_entry', methods=['POST'])
def add_entry():
    user_id = session.get('user_id')
    data = request.get_json()  # 接收 JSON 数据
    content = data.get('content')
    wechat_id = data.get('wechat_id')
    gender = data.get('gender')

    if not user_id or not content or not gender:
        return jsonify({"error": "缺失信息"}), 400

    try:
        new_entry = BlindBoxEntry(
            user_id=user_id,
            content=content,
            wechat_id=wechat_id,
            gender=gender,
            count=50,
        )
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {e}"}), 500

    return jsonify({"message": "纸条成功放入盲盒"}), 200

import random

@app.route('/get_entry', methods=['GET'])
def get_entry():
    gender = request.args.get('gender')
    if not gender:
        return jsonify({"error": "没有选择性别"}), 400

    try:
        update_scores()
        # 获取所有指定性别的纸条
        entries = BlindBoxEntry.query.filter_by(gender=gender).all()

        if not entries:
            return jsonify({"error": "盲盒中的纸条全部被抽完啦！"}), 404
        
        # 计算总权重
        total_weight = sum(entry.score for entry in entries)
        
        if total_weight == 0:
            return jsonify({"error": "所有纸条的权重为零，无法抽取"}), 400
        
        # 按照权重进行加权随机抽取
        random_choice = random.choices(entries, weights=[entry.score for entry in entries], k=1)[0]

        # 增加抽取计数
        random_choice.count -= 1

        if random_choice.count == 0:
            # 达到抽取限制后删除纸条
            db.session.delete(random_choice)

        db.session.commit()

        # 返回纸条内容
        response_data = {
            "content": random_choice.content,
            "wechat_id": random_choice.wechat_id,
            "remaining_draws": random_choice.count  # 剩余抽取次数
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"数据库错误: {e}"}), 500
    
@app.route('/get_usernames', methods=['GET'])
def get_usernames():
    # 获取当前登录的用户ID
    current_user_id = session.get('user_id')
    
    if current_user_id is None:
        return jsonify({'error': 'User not logged in'}), 401

    # 查询 BlindBox 表，获取对应的 username
    user_info = UserInfo.query.filter_by(id=current_user_id).first()
    
    if user_info:
        return jsonify({'username': user_info.username})
    else:
        return jsonify({'error': 'User info not found'}), 404




if __name__ == '__main__':
    app.run(debug=True)
