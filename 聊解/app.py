from flask import Flask, render_template, request, redirect, url_for, flash, session
import MySQLdb
import bcrypt
import os
import re
from werkzeug.utils import secure_filename
from functools import wraps
import secrets

# Flask 应用配置
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# 数据库连接配置
db = MySQLdb.connect(host='localhost', user='root', passwd='@Zx2022611039', db='ChatApp', charset='utf8mb4')

# 上传文件配置
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 限制文件最大为16MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 如果上传文件夹不存在，则创建
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 工具函数
def allowed_file(filename):
    """检查文件是否符合上传要求"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_input(input_value):
    """去除用户输入中的特殊字符"""
    return re.sub(r"[^\w\s]", "", input_value)

def login_required(f):
    """装饰器：检查用户是否已登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_friend_usernames(current_user_id):
    """获取好友列表的用户名"""
    with db.cursor() as cursor:
        cursor.execute("SELECT friend_id FROM Friends WHERE user_id=%s", (current_user_id,))
        friends = cursor.fetchall()
        friend_usernames = []
        for friend in friends:
            cursor.execute("SELECT username FROM Users WHERE id=%s", (friend[0],))
            username_result = cursor.fetchone()
            if username_result:
                friend_usernames.append((friend[0], username_result[0]))
    return friend_usernames

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册功能"""
    if request.method == 'POST':
        username = sanitize_input(request.form['username'])
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        with db.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", (username, hashed_password))
                db.commit()
                flash('注册成功！请登录。', 'success')
                return redirect(url_for('login'))
            except MySQLdb.IntegrityError:
                flash('用户名已被使用，请选择其他用户名。', 'error')
            except Exception as e:
                flash(f'注册失败：{str(e)}', 'error')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录功能"""
    if request.method == 'POST':
        username = sanitize_input(request.form['username'])
        password = request.form['password']

        with db.cursor() as cursor:
            cursor.execute("SELECT id, password FROM Users WHERE username=%s", (username,))
            user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]
            session.permanent = True
            flash('登录成功！', 'success')
            return redirect(url_for('main_page'))
        else:
            flash('用户名或密码错误！', 'error')

    return render_template('login.html')

@app.route('/main_page')
def main_page():
    current_user_id = session.get('user_id')

    try:
        with db.cursor() as cursor:
            # 查询所有用户（排除当前用户）
            cursor.execute("SELECT id, username FROM Users WHERE id != %s", (current_user_id,))
            users = cursor.fetchall()

            friend_usernames = get_friend_usernames(current_user_id)

        return render_template('main_page.html', users=users, friends=friend_usernames)

    except Exception as e:
        flash("获取用户列表时出现问题，请稍后重试。", 'error')
        print(f"Error: {e}")
        return redirect(url_for('main_page'))

@app.route('/add_friend', methods=['POST'])
def add_friend():
    friend_id = request.form.get('friend_id')
    if friend_id:
        # 在此处理添加好友逻辑
        return f"好友 {friend_id} 已添加！", 200
    return "无效的好友 ID", 400

@app.route('/chat_with_friend/<int:friend_id>', methods=['GET'])
def chat_with_friend(friend_id):
    """显示与好友聊天的界面"""
    current_user_id = session.get('user_id')

    try:
        with db.cursor() as cursor:
            # 获取好友的用户名
            cursor.execute("SELECT username FROM Users WHERE id=%s", (friend_id,))
            friend_result = cursor.fetchone()
            friend_username = friend_result[0] if friend_result else "未知用户"
            
            # 获取聊天记录
            cursor.execute(
                "SELECT content, sender_id, created_at FROM Messages "
                "WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s) "
                "ORDER BY created_at ASC",
                (current_user_id, friend_id, friend_id, current_user_id)
            )
            messages = cursor.fetchall()

        # 获取当前用户的好友列表
        friend_usernames = get_friend_usernames(current_user_id)

        # 渲染聊天页面模板
        return render_template('chat.html', friends=friend_usernames, friend_username=friend_username, messages=messages)

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        flash("聊天功能出现问题，请稍后重试。", 'error')
        return redirect(url_for('main_page'))

@app.route('/chat/<int:friend_id>', methods=['GET', 'POST'])
@login_required
def chat(friend_id):
    """聊天功能"""
    current_user_id = session.get('user_id')
    try:
        with db.cursor() as cursor:
            if request.method == 'POST':
                emoji = request.files.get('emoji')
                group_name = request.form.get('group_name', '默认').strip()
                message = sanitize_input(request.form.get('message', '').strip())

                if emoji and allowed_file(emoji.filename):
                    filename = secure_filename(emoji.filename[:100])
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    if emoji.content_length > MAX_FILE_SIZE:
                        flash("文件大小超过限制。", 'error')
                        return redirect(request.url)

                    emoji.save(filepath)
                    cursor.execute(
                        "INSERT INTO UserEmojis (user_id, group_name, filename) VALUES (%s, %s, %s)",
                        (current_user_id, group_name, filename)
                    )
                    db.commit()
                    message = f"emoji:{filename}"

                if message:
                    cursor.execute(
                        "INSERT INTO Messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
                        (current_user_id, friend_id, message)
                    )
                    db.commit()

            cursor.execute("SELECT username FROM Users WHERE id=%s", (friend_id,))
            friend_username = cursor.fetchone()[0] if cursor.fetchone() else "未知用户"

            cursor.execute(
                "SELECT content, sender_id, created_at FROM Messages "
                "WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s) "
                "ORDER BY created_at ASC",
                (current_user_id, friend_id, friend_id, current_user_id)
            )
            messages = cursor.fetchall()

            cursor.execute(
                "SELECT filename, group_name FROM UserEmojis WHERE user_id=%s ORDER BY created_at DESC",
                (current_user_id,)
            )
            emojis = cursor.fetchall()

        friend_usernames = get_friend_usernames(current_user_id)

        return render_template('chat.html', friends=friend_usernames, friend_username=friend_username, messages=messages, emojis=emojis)

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        flash("聊天功能出现问题，请稍后重试。", 'error')
        return redirect(url_for('main_page'))

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True)
