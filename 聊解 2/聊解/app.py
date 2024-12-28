from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_sqlalchemy import SQLAlchemy
import secrets
import random
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40Zx2022611039@localhost:3306/mydate'
#db = MySQLdb.connect(host='localhost', user='root', passwd='@Zx2022611039', db='mydate', charset='utf8mb4')
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
            'grade': self.grade
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
#信息表格
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    sent_count = db.Column(db.Integer, default=0)  # 记录发送的消息数量
 
#自动生成表格    
with app.app_context():
    db.create_all() 
#随机生成 id    
def generate_random_id():
    return str(uuid.uuid4())  # 生成 36 位随机 UUID
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

#显示所有用户（汕恋部分）
@app.route('/main_page', methods=['GET'])
def main_page():
    current_user_id = session.get('user_id')
    if current_user_id is None:
        return redirect(url_for('login'))
    user_info = UserInfo.query.filter_by(id=current_user_id).first()
    # 使用 SQLAlchemy 查询所有用户，排除当前用户
    users = UserInfo.query.all()  # 获取所有用户，排除当前用户

    # 如果没有找到用户信息，直接重定向到完善信息页面
    if not user_info:
        return render_template('main_page.html',users=users,user_info_missing = True)
    
        
    return render_template('main_page.html', users=users,user_info_missing = False)

    
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
            query = query.filter(getattr(User, key) == value)

    users = query.all()
    return [user.to_dict() for user in users]


@app.route('/chat', methods=['GET', 'POST'])
@app.route('/chat/<receiver_id>', methods=['GET', 'POST'])
def chat(receiver_id=None):
    current_user_id = session.get('user_id')
    # 如果用户未登录，直接返回空页面
    if not current_user_id:
        return redirect(url_for('login'))

    # 获取好友列表
    friends = Friend.query.filter_by(user_id=current_user_id).all()
    friend_usernames = [
        (UserInfo.query.get(friend.friend_id).id, UserInfo.query.get(friend.friend_id).username)
        for friend in friends if UserInfo.query.get(friend.friend_id)
    ]

    # 获取已聊对象列表
    chathistories = ChatHistory.query.filter_by(user_id=current_user_id).all()
    chathistories_usernames = [
        (UserInfo.query.get(chathistory.chat_partner_id).id, UserInfo.query.get(chathistory.chat_partner_id).username)
        for chathistory in chathistories if UserInfo.query.get(chathistory.chat_partner_id)
    ]

    # 如果未指定接收者，展示好友和已聊对象列表
    if not receiver_id:
        return render_template(
            'chat.html',
            friends=friend_usernames,
            chatted_users=chathistories_usernames,
            messages=[]
        )

    # 检查是否为好友关系
    is_friend = Friend.query.filter(
        ((Friend.user_id == current_user_id) & (Friend.friend_id == receiver_id)) |
        ((Friend.user_id == receiver_id) & (Friend.friend_id == current_user_id))
    ).first()

    # 检查是否为已聊对象关系
    is_chathistory = ChatHistory.query.filter(
        ((ChatHistory.user_id == current_user_id) & (ChatHistory.chat_partner_id == receiver_id)) |
        ((ChatHistory.user_id == receiver_id) & (ChatHistory.chat_partner_id == current_user_id))
    ).first()

    # 获取历史消息
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.created_at).all()

    # 处理消息发送
    if request.method == 'POST':
        new_message = request.form.get('message', '').strip()
        if new_message:
            try:
                # 如果不是好友，添加到历史聊天列表
                if not is_chathistory:
                    new_entry1 = ChatHistory(user_id=current_user_id, chat_partner_id=receiver_id)
                    new_entry2 = ChatHistory(user_id=receiver_id, chat_partner_id=current_user_id)
                    db.session.add(new_entry1)
                    db.session.add(new_entry2)

                # 检查消息发送限制
                current_user_messages_count = Message.query.filter_by(
                    sender_id=current_user_id, receiver_id=receiver_id
                ).count()
                receiver_messages_count = Message.query.filter_by(
                    sender_id=receiver_id, receiver_id=current_user_id
                ).count()

                if current_user_messages_count >= 3 and receiver_messages_count == 0:
                    flash("在对方回复你之前只能发送三条消息。")
                    db.session.rollback()  # 回滚未提交的事务
                    return redirect(url_for('chat', receiver_id=receiver_id))

                # 保存新消息
                message = Message(
                    sender_id=current_user_id,
                    receiver_id=receiver_id,
                    content=new_message,
                    created_at=db.func.current_timestamp()
                )
                db.session.add(message)
                db.session.commit()
                flash('消息发送成功！')
            except Exception as e:
                db.session.rollback()
                flash(f'发送消息失败：{e}')
        else:
            flash('消息不能为空！')

    # 渲染聊天页面
    receiver_user = UserInfo.query.get(receiver_id)
    if not receiver_user:
        return redirect(url_for('chat'))  # 如果接收者不存在，返回聊天列表

    return render_template(
        'chat.html',
        friends=friend_usernames,
        chatted_users=chathistories_usernames,
        receiver_username=receiver_user.username,
        receiver_id=receiver_id,
        messages=[(msg.content, msg.sender_id) for msg in messages]
    )



if __name__ == '__main__':
    app.run(debug=True)
