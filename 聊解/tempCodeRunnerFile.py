@app.route('/chat/<int:friend_id>', methods=['GET', 'POST'])
@login_required
def chat_with_friend(friend_id):
    current_user_id = session.get('user_id')

    with db.cursor() as cursor:
        if request.method == 'POST':
            # 上传表情包
            if 'emoji' in request.files:
                emoji = request.files['emoji']
                if emoji and allowed_file(emoji.filename):
                    filename = secure_filename(emoji.filename[:100])  # 限制文件名长度
                    emoji.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    message = f"emoji:{filename}"
                else:
                    flash('无效的表情包文件格式！', 'error')
                    return redirect(request.url)
            else:
                # 普通文本消息
                message = sanitize_input(request.form.get('message', '').strip())

            if message:
                try:
                    cursor.execute(
                        "INSERT INTO Messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
                        (current_user_id, friend_id, message)
                    )
                    db.commit()
                except Exception as e:
                    flash(f'发送消息失败：{str(e)}', 'error')

        # 获取好友的用户名
        cursor.execute("SELECT username FROM Users WHERE id=%s", (friend_id,))
        friend_username = cursor.fetchone()[0]

        # 获取当前用户与好友之间的消息
        cursor.execute(
            "SELECT content, sender_id, created_at FROM Messages "
            "WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s) "
            "ORDER BY created_at ASC",
            (current_user_id, friend_id, friend_id, current_user_id)
        )
        messages = cursor.fetchall()

        # 获取好友列表
        cursor.execute("SELECT friend_id FROM Friends WHERE user_id=%s", (current_user_id,))
        friends = cursor.fetchall()
        friend_usernames = []
        for friend in friends:
            cursor.execute("SELECT id, username FROM Users WHERE id=%s", (friend[0],))
            friend_usernames.append(cursor.fetchone())

    return render_template(
        'chat.html',
        friends=friend_usernames,
        friend_username=friend_username,
        messages=messages,
        friend_id=friend_id
    )