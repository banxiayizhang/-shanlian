let currentReceiverId = null;  // 当前接收消息的用户 ID   
let currentUserId = null;      // 当前用户的 ID

// 获取当前用户的 ID
async function fetchCurrentUserId() {
    try {
        const response = await fetch('/get_current_user');
        const data = await response.json();
        currentUserId = data.user_id;  // 设置当前用户的 ID
        console.log('当前用户 ID:', currentUserId);  // 调试输出
    } catch (error) {
        console.error('获取当前用户 ID 失败:', error);
    }
}

// 页面加载时获取当前用户的 ID
document.addEventListener('DOMContentLoaded', async function() {
    await fetchCurrentUserId();  // 获取当前用户的 ID
    setupFriendClickListener(); // 确保好友点击事件绑定
});


function setupFriendClickListener() {
    const friendListItems = document.querySelectorAll('.friend-list li');
    
    friendListItems.forEach(item => {
        item.addEventListener('click', async function() {
            // 获取选中的好友 ID
            const receiverId = this.getAttribute('data-chat-id');
            const receiverName = this.querySelector('.friend-item').textContent.trim();
            
            console.log('Receiver ID:', receiverId);  // 输出调试信息
            
            if (!receiverId || receiverId === 'null') {
                console.log('Error: Invalid receiver ID');
                return;
            }
            
            // 更新聊天区的标题
            const chatHeader = document.getElementById('chat-header');
            chatHeader.textContent = `与 ${receiverName} 聊天中...`;
            chatHeader.setAttribute('data-chat-id', receiverId);  // 设置正确的 receiverId
            console.log('Updated Receiver ID in chat header:', receiverId);  // 输出更新后的 receiverId

            // 设置选中的好友项的样式
            friendListItems.forEach(friend => friend.classList.remove('active'));
            this.classList.add('active');

            // 加载聊天记录
            loadChat(receiverId, receiverName);
        });
    });
}

// 修改 loadChat 函数，确保正确传递 receiverId
function loadChat(receiverId, receiverName) {
    console.log(`Loading chat with receiver ID: ${receiverId} and name: ${receiverName}`);
    
    // 确保调用的后端 API 能够处理 receiver_id，并返回聊天记录
    fetch(`/get_messages?receiver_id=${receiverId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`服务器返回错误：${response.status}`);
        }
        return response.text();  // 先返回文本格式
    })
    .then(text => {
        try {
            const data = JSON.parse(text);  // 尝试将文本解析为 JSON
            if (data.status === 'success') {
                const messages = data.messages;
                const chatMessages = document.getElementById('chat-messages');
                chatMessages.innerHTML = '';  // 清空当前聊天记录

                // 按照时间戳升序排序消息（最旧的在前，最新的在后）
                messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

                // 按顺序将所有消息添加到底部
                messages.forEach(message => {
                    const messageClass = message.sender_id === currentUserId ? 'my-message' : 'other-message';
                    addMessageToChat(messageClass, message.message);
                });

                // 让聊天区域滚动到底部
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                console.log('无法加载历史消息');
            }
        } catch (error) {
            console.error('解析 JSON 时出错:', error);
            alert('加载聊天记录时出错，服务器返回非 JSON 格式数据');
        }
    })
    .catch(error => {
        console.error('加载聊天记录时出错:', error);
    });

}

// 自动调整 textarea 高度
function autoResizeTextarea() {
    // 获取消息输入框元素
const messageInput = document.getElementById('message-input');

// 添加一个输入事件监听器来动态调整输入框的大小
messageInput.addEventListener('input', function () {
    // 重置高度
    messageInput.style.height = 'auto';
    
    // 设置新的高度
    messageInput.style.height = messageInput.scrollHeight + 'px';
});
}

// 页面加载时绑定事件
document.addEventListener('DOMContentLoaded', function () {
    autoResizeTextarea();
});


function addMessageToChat(messageClass, message) {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageElement = document.createElement('div');
    messageElement.classList.add(messageClass);

    // 创建一个包含文本的 div 元素
    const textElement = document.createElement('div');
    textElement.classList.add('message-text');
    textElement.textContent = message;

    // 将文本添加到消息框中
    messageElement.appendChild(textElement);

    // 将消息框添加到聊天区域
    chatMessages.appendChild(messageElement);

    // 让聊天区域滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// 发送消息
function sendMessage(event) {
    event.preventDefault();  // 阻止表单默认提交

    let messageInput = document.getElementById('message-input');
    let message = messageInput.value.trim();
    
    if (message === "") {
        alert("请输入消息！");
        return;
    }

    // 获取接收者 ID
    let receiverId = document.getElementById('chat-header').getAttribute('data-chat-id');
    console.log('Receiver ID from chat header:', receiverId);  // 调试输出 receiverId

    if (!receiverId) {
        alert("请选择一个好友进行聊天！");
        return;
    }

    // 发送消息到后端
    fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            receiver_id: receiverId,  // 确保发送正确的 receiver_id
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            messageInput.value = '';  // 清空输入框

            // 显示发送的消息
            addMessageToChat('my-message', message);
        } else {
            console.log('消息发送失败');
        }
    })
    .catch(error => {
        console.error('发送消息时出现错误:', error);
    });
}

function addFriend() {
    const phoneNumber = document.getElementById('phone_number').value.trim();  // 获取输入的手机号并去掉空格
    if (!phoneNumber) {
        alert('手机号不能为空');
        return;
    }

    // 简单的手机号格式验证（例如，假设手机号应为 11 位数字）
    const phonePattern = /^[0-9]{11}$/;
    if (!phonePattern.test(phoneNumber)) {
        alert('请输入有效的手机号');
        return;
    }

    fetch('/add_friend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',  // 确保请求头为 application/json
        },
        body: JSON.stringify({
            user_id: currentUserId,  // 当前用户的 ID
            phone_number: phoneNumber  // 手机号码
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('好友添加成功');

            // 更新好友列表
            const friendList = document.getElementById('friend-list');
            const newFriend = data.friends.find(friend => friend.phone_number === phoneNumber);  // 查找新添加的好友

            if (newFriend) {
                const li = document.createElement('li');
                li.classList.add('friend-item');
                li.dataset.chatId = newFriend.id;  // 设置好友ID
                li.textContent = newFriend.username;  // 显示好友用户名
                friendList.appendChild(li);
            }
        } else {
            alert('好友添加失败: ' + data.message);
        }
    })
    .catch(error => {
        console.error('添加好友时发生错误:', error);
        alert('添加好友失败，请稍后重试');
    });
}
// 表情选择器相关
function toggleEmojiPicker() {
    const emojiPicker = document.getElementById('emoji-picker');
    emojiPicker.style.display = emojiPicker.style.display === 'block' ? 'none' : 'block';
}

function addEmoji(emoji) {
    const messageInput = document.getElementById('message-input');
    messageInput.value += emoji;
    toggleEmojiPicker();  // 关闭表情选择器
}
async function fetchCurrentUserId() {
    try {
        const response = await fetch('/get_current_user');
        const data = await response.json();
        currentUserId = data.user_id;  // 设置当前用户的 ID
        console.log('当前用户 ID:', currentUserId);  // 调试输出
    } catch (error) {
        console.error('获取当前用户 ID 失败:', error);
    }
}

async function loadChattedUsers() {
    try {
        const response = await fetch('/get_chat_relationships');
        const data = await response.json();

        if (data.status === 'success') {
            const chattedList = document.getElementById('chatted-list');
            chattedList.innerHTML = '';  // 清空现有的列表

            data.chatted_users.forEach(user => {
                const li = document.createElement('li');
                li.innerHTML = `<a href="/chat?receiver_id=${user.id}">${user.username}</a>`;
                chattedList.appendChild(li);
            });
        } else {
            console.error('无法加载对话列表');
        }
    } catch (error) {
        console.error('加载对话列表时出错:', error);
    }
}

// 添加消息到聊天区域
function addMessageToChat(messageClass, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.classList.add(messageClass);

    // 创建一个包含文本的 div 元素，限制每行最多 10 个字符
    const textElement = document.createElement('div');
    textElement.classList.add('message-text');
    textElement.textContent = message;

    // 将文本添加到消息框中
    messageElement.appendChild(textElement);

    // 将消息框添加到聊天区域
    chatMessages.appendChild(messageElement);

    // 让聊天区域滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
