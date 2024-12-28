// 发送消息
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const messageText = messageInput.value.trim();

    if (messageText) {
        // 发送 POST 请求
        sendRequest('/send_message', 'POST', { message: messageText })
            .then(data => {
                if (data.success) {
                    messageInput.value = ''; // 清空输入框
                    loadMessages(); // 刷新消息列表
                } else {
                    handleError(data.error);
                }
            })
            .catch(handleError);
    }
}

// 加载消息
function loadMessages() {
    // 请求最新的消息
    sendRequest('/get_messages', 'GET')
        .then(data => {
            const messagesContainer = document.getElementById('messages');
            updateMessages(messagesContainer, data.messages);
        })
        .catch(handleError);
}

// 通用的请求函数
function sendRequest(url, method, body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    };

    if (body) {
        options.body = new URLSearchParams(body).toString();
    }

    return fetch(url, options)
        .then(response => response.json())
        .catch(error => {
            throw new Error('Network error: ' + error.message);
        });
}

// 更新消息列表
function updateMessages(container, messages) {
    container.innerHTML = ''; // 清空当前消息

    messages.forEach(msg => {
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        messageElement.textContent = msg;
        container.appendChild(messageElement);
    });

    // 滚动到最新消息
    container.scrollTop = container.scrollHeight;
}

// 错误处理
function handleError(error) {
    console.error('Error:', error || 'Unknown error');
    // 可以考虑显示用户友好的错误信息，例如：
    alert('Something went wrong, please try again later.');
}

// 定时刷新消息，每秒调用一次 loadMessages
setInterval(loadMessages, 1000);
