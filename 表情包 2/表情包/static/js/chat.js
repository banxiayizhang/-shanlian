// 保存当前聊天对象的信息
let currentReceiverId = null;  
let currentUserId = null;

// 获取当前用户的 ID
function fetchCurrentUserId() {
    fetch('/get_current_user')
        .then(response => response.json())
        .then(data => {
            currentUserId = data.user_id;
        })
        .catch(error => {
            console.error('获取当前用户 ID 失败:', error);
        });
}

// 页面加载时获取当前用户的 ID
document.addEventListener('DOMContentLoaded', function() {
    fetchCurrentUserId();
});

function selectFriend(receiverId, receiverName) {
    // 更新聊天区的标题
    const chatHeader = document.getElementById('chat-header');
    chatHeader.querySelector('h3').textContent = `与 ${receiverName} 聊天中...`;
    chatHeader.setAttribute('data-chat-id', receiverId);

    // 清空历史消息区域
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = ''; // 清空聊天记录

    // 加载聊天记录
    loadChat(receiverId, receiverName);

    // 发送到后端并添加到已聊对象列表
    fetch('/add_to_chatted_list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chatted_user_id: receiverId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 添加到已聊对象列表（前端）
            addToChattedList(receiverId, receiverName);
        }
    })
    .catch(error => console.error('添加到已聊对象列表失败:', error));
}

// 获取已聊对象列表
function getChattedUsers() {
    fetch('/get_chatted_users')
        .then(response => response.json())
        .then(data => {
            if (data.users) {
                const chattedList = document.getElementById('chatted-list').querySelector('ul');
                chattedList.innerHTML = '';  // 清空现有列表
                data.users.forEach(user => {
                    addToChattedList(user.id, user.username);  // 逐个添加到已聊对象列表
                });
            }
        })
        .catch(error => console.error('获取已聊对象失败:', error));
}

// 每次加载页面时，获取已聊对象
document.addEventListener('DOMContentLoaded', function() {
    getChattedUsers();  // 加载已聊对象
});

// 每次加载页面时，获取已聊对象
document.addEventListener('DOMContentLoaded', function() {
    getChattedUsers();  // 加载已聊对象
});


function addToChattedList(receiverId, receiverName) {
    const chattedList = document.getElementById('chatted-list').querySelector('ul');
    
    // 检查该好友是否已经在已聊对象列表中
    const existingItem = Array.from(chattedList.children).find(item => item.getAttribute('data-chat-id') === receiverId);
    if (existingItem) {
        console.log(`${receiverName} 已经在已聊对象列表中`);
        return; // 如果已经存在，跳过添加
    }

    // 创建新的已聊对象列表项
    const newItem = document.createElement('li');
    newItem.setAttribute('data-chat-id', receiverId);
    newItem.innerHTML = `<a href="javascript:void(0)" onclick="selectFriend('${receiverId}', '${receiverName}')">${receiverName}</a>`;
    
    // 为新项添加点击事件
    newItem.querySelector('a').addEventListener('click', function() {
        selectFriend(receiverId, receiverName);
    });

    // 将新项添加到已聊对象列表
    chattedList.appendChild(newItem);
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

function uploadEmoji(event) {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append("image", file);  // 确保字段名与后端一致

        // 发送图片到后端
        fetch('/upload_image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === "图片上传成功！") {
                const messageInput = document.getElementById('message-input');
                const messageContainer = document.getElementById('chat-messages');  // 假设消息区域的 id 为 chat-messages

                // 创建 img 元素来显示图片
                const imgElement = document.createElement('img');
                imgElement.src = data.file_url;  // 返回的图片路径
                //imgElement.style.width = '80px';
                //imgElement.style.height = '80px';

                // 将图片添加到聊天区域
                const newMessage = document.createElement('div');
                newMessage.classList.add('my-message');  // 假设这是当前用户的消息
                newMessage.appendChild(imgElement);  // 将图片插入消息框

                // 将新消息添加到消息区域
                messageContainer.appendChild(newMessage);

                // 滚动到消息底部
                messageContainer.scrollTop = messageContainer.scrollHeight;
            } else {
                alert('图片上传失败');
            }
        })
        .catch(error => {
            console.error('图片上传出错:', error);
            alert('图片上传失败');
        });
    }
}

// 加载聊天记录
function loadChat(receiverId, receiverName) {
    fetch(`/get_messages?receiver_id=${receiverId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const messages = data.messages;
                const chatMessages = document.getElementById('chat-messages');
                chatMessages.innerHTML = ''; // 清空当前聊天记录

                // 将历史消息显示在聊天区
                messages.forEach(message => {
                    const messageClass = message.sender_id === currentUserId ? 'my-message' : 'other-message';
                    addMessageToChat(messageClass, message.message);
                });

                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        })
        .catch(error => {
            console.error('加载聊天记录时出错:', error);
        });
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
            receiver_id: receiverId,
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

// 添加消息到聊天区
function addMessageToChat(messageClass, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.classList.add(messageClass);
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
