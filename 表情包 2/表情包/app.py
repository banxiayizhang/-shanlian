from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import pymysql
import os
from werkzeug.utils import secure_filename

app = Flask(__name__) 
app.secret_key = 'your_secret_key'  # 用于会话管理，确保每个用户会话是独立的
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@Zx2022611039@localhost/chat_db'  # 你的数据库 URI
app.config['STATIC_FOLDER'] = 'static'

# 定义允许的文件扩展名和上传文件夹
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(app.config['STATIC_FOLDER'], 'uploads')

# 如果上传文件夹不存在，则创建它
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bcrypt = Bcrypt(app)

# 获取数据库连接
def get_db_connection():
    return pymysql.connect(
        host='localhost',  # 替换为你的主机
        user='root',       # 你的 MySQL 用户名
        password='@Zx2022611039',  # 你的 MySQL 密码
        db='chat_db',      # 你的数据库名称
        cursorclass=pymysql.cursors.DictCursor  # 使用字典游标，以便查询结果为字典格式
    )

# 判断文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('register.html')  # 这里你可以替换为你的主页模板

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册功能"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 校验用户名和密码长度
        if len(username) < 0 or len(password) < 6:
            flash("用户名或密码长度不符合要求", 'error')
            return render_template('register.html')

        # 密码加密
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 插入新用户
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))
        except pymysql.MySQLError:
            flash('用户名已被使用，请选择其他用户名。', 'error')
        except Exception as e:
            flash(f'注册失败：{str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录功能"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 连接到数据库
        conn = get_db_connection()
        cursor = conn.cursor()

        # 查询用户名对应的用户信息
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            # 使用 bcrypt 验证密码
            if bcrypt.check_password_hash(user['password'], password):
                # 登录成功，记录用户ID到 session
                session['user_id'] = user['id']
                session.permanent = True  # 会话保持，避免会话过期
                flash('登录成功！', 'success')
                return redirect(url_for('users_list'))  # 登录后跳转到聊天界面
            else:
                flash('用户名或密码错误！', 'error')
        else:
            flash('用户名不存在！', 'error')

        cursor.close()
        conn.close()

    return render_template('login.html')

@app.route('/add_to_chatted_list', methods=['POST'])
def add_to_chatted_list():
    data = request.get_json()

    current_user_id = data.get('current_user_id')
    chatted_user_id = data.get('chatted_user_id')

    if not current_user_id or not chatted_user_id:
        return jsonify({"error": "缺少必要的参数"}), 400

    # 将该聊天对象添加到数据库
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO chatted_users (user_id, chatted_user_id) 
        VALUES (%s, %s)
    """, (current_user_id, chatted_user_id))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"status": "success"})


@app.route('/get_chatted_users', methods=['GET'])
def get_chatted_users():
    # 获取当前用户ID
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({"error": "用户未登录"}), 401

    try:
        # 获取数据库连接
        connection = get_db_connection()
        cursor = connection.cursor()

        # 查询当前用户的已聊对象
        cursor.execute("""
            SELECT u.id, u.username
            FROM chatted_users cu
            JOIN users u ON cu.chatted_user_id = u.id
            WHERE cu.user_id = %s
        """, (current_user_id,))

        chatted_users = cursor.fetchall()

        # 关闭数据库连接
        cursor.close()
        connection.close()

        # 如果没有已聊对象，返回空列表
        if not chatted_users:
            return jsonify({'users': []})

        # 格式化返回结果
        users_list = [{'id': user[0], 'username': user[1]} for user in chatted_users]

        return jsonify({'users': users_list})

    except Exception as e:
        # 错误处理
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

@app.route('/users_list')
def users_list():
    """显示所有用户的用户名"""
    # 获取数据库连接
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 查询所有用户名
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()
    except Exception as e:
        flash(f"查询失败: {str(e)}", 'error')
        users = []

    finally:
        cursor.close()
        conn.close()

    # 渲染页面，将查询到的用户传递给模板
    return render_template('users_list.html', users=users)

@app.route('/chat')
def chat():
    """聊天功能"""
    if 'user_id' not in session:
        flash("请先登录", 'error')
        return redirect(url_for('login'))

    # 获取当前用户的好友列表
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username 
        FROM users 
        WHERE id IN (SELECT friend_id FROM friends WHERE user_id = %s)
    """, (session['user_id'],))
    friends = cursor.fetchall()

    # 获取当前用户与某个好友的聊天记录
    receiver_id = request.args.get('receiver_id')
    messages = []

    # 更新已聊对象列表
    if 'chatted_users' not in session:
        session['chatted_users'] = []

    if receiver_id:
        # 添加到已聊对象列表
        if receiver_id not in session['chatted_users']:
            session['chatted_users'].append(receiver_id)
            session.modified = True

        # 查询聊天记录
        cursor.execute("""
            SELECT sender_id, receiver_id, message, timestamp 
            FROM messages 
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY timestamp
        """, (session['user_id'], receiver_id, receiver_id, session['user_id']))
        messages = cursor.fetchall()

        # 获取聊天对象的用户信息
        cursor.execute("SELECT username FROM users WHERE id = %s", (receiver_id,))
        chatted_user = cursor.fetchone()

    # 获取已聊对象
    cursor.execute("SELECT id, username FROM users WHERE id IN (%s)", (', '.join(map(str, session['chatted_users'])),))
    chatted_users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('chat_combined.html', 
                           friends=friends, 
                           messages=messages, 
                           receiver_id=receiver_id, 
                           chatted_users=chatted_users)


@app.route('/add_friend', methods=['POST'])
def add_friend():
    """添加好友"""
    if 'user_id' not in session:
        return jsonify({'error': '用户未登录'}), 401

    friend_id = request.form['friend_id']
    if not friend_id:
        return jsonify({'error': '好友ID不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # 查询好友是否存在
    cursor.execute("SELECT id FROM users WHERE id = %s", (friend_id,))
    friend = cursor.fetchone()

    if not friend:
        return jsonify({'error': '好友不存在'}), 404

    # 检查是否已经是好友
    cursor.execute("SELECT * FROM friends WHERE user_id = %s AND friend_id = %s", (session['user_id'], friend_id))
    existing_friendship = cursor.fetchone()

    if existing_friendship:
        return jsonify({'status': 'error', 'message': '已经是好友'}), 400

    # 插入新的好友关系
    cursor.execute("INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)", (session['user_id'], friend_id))
    conn.commit()

    cursor.close()
    conn.close()

    # 好友添加成功后，重定向到聊天页面，刷新好友列表
    flash('好友添加成功！', 'success')
    return redirect(url_for('chat'))

# 图片上传接口
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "没有文件部分"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    
    if file and allowed_file(file.filename):
        try:
            # 保存文件到上传目录
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            # 返回图片访问的相对路径
            return jsonify({"message": "图片上传成功！", "file_url": f"/static/uploads/{file.filename}"}), 200
        except Exception as e:
            return jsonify({"error": f"上传失败: {str(e)}"}), 500

    return jsonify({"error": "文件类型不支持"}), 400

@app.route('/send_message', methods=['POST'])
def send_message():
    """发送消息"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    data = request.get_json()
    receiver_id = data.get('receiver_id')
    message = data.get('message')

    if not receiver_id or not message:
        return jsonify({'status': 'error', 'message': '缺少必要的参数'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 判断是否是好友
        cursor.execute("""
            SELECT * 
            FROM friends 
            WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
        """, (session['user_id'], receiver_id, receiver_id, session['user_id']))
        is_friend = cursor.fetchone()

        if is_friend:
            # 好友聊天没有限制
            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, message) 
                VALUES (%s, %s, %s)
            """, (session['user_id'], receiver_id, message))
        else:
            # 已聊对象聊天限制 5 条消息
            cursor.execute("""
                SELECT COUNT(*) 
                FROM messages 
                WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            """, (session['user_id'], receiver_id, receiver_id, session['user_id']))
            message_count = cursor.fetchone()["COUNT(*)"]

            if message_count >= 5:
                return jsonify({'status': 'error', 'message': '已聊对象最多只能发送5条消息'}), 400

            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, message) 
                VALUES (%s, %s, %s)
            """, (session['user_id'], receiver_id, message))

        conn.commit()

        cursor.execute("""
            SELECT m.sender_id, m.receiver_id, m.message, m.timestamp, u.username
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.sender_id = %s AND m.receiver_id = %s
            ORDER BY m.timestamp DESC
            LIMIT 1
        """, (session['user_id'], receiver_id))
        message_data = cursor.fetchone()

        return jsonify({
            'status': 'success',
            'message': '消息发送成功',
            'message_data': message_data
        }), 200
    except pymysql.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# 新增的路由，处理获取当前用户信息
@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    return jsonify({'user_id': session['user_id']})

# 新增的路由，获取与某个用户的聊天记录
@app.route('/get_messages', methods=['GET'])
def get_messages():
    """获取历史消息"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': '请先登录'}), 401

    # 获取查询参数
    receiver_id = request.args.get('receiver_id')

    if not receiver_id:
        return jsonify({'status': 'error', 'message': '缺少接收者ID'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 查询与当前聊天相关的所有消息
        cursor.execute("""
            SELECT m.sender_id, m.receiver_id, m.message, m.timestamp, u.username
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = %s AND m.receiver_id = %s) OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.timestamp DESC
        """, (session['user_id'], receiver_id, receiver_id, session['user_id']))
        messages = cursor.fetchall()

        # 返回所有历史消息
        return jsonify({
            'status': 'success',
            'messages': messages
        }), 200
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
