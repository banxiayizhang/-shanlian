//----------------------------------------------------------改👇

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



//------------------------------------------------------改👆

document.addEventListener('DOMContentLoaded', async function () {
    const filterForm = document.getElementById('filter-form');
    const cardsContainer = document.getElementById('cards-container');

    //----------------------------------------------改👇
    await fetchCurrentUserId();  // 获取当前用户的 ID
    //----------------------------------------------改👆

    // 处理滤镜选项点击事件
    filterForm.querySelectorAll('input[type="radio"]').forEach(input => {
        input.addEventListener('click', function () {
            // 改变点击后的颜色
            this.style.backgroundColor = '#ccc';
            setTimeout(() => {
                this.style.backgroundColor = ''; // 一段时间后恢复原状
            }, 300);
        });
    });

    // 初始化时显示所有卡片
    loadAllCards();

    // 监听表单提交事件
    filterForm.addEventListener('submit', function (event) {
        event.preventDefault(); // 阻止默认的表单提交行为
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData).toString();
        filterCards(params);
    });

    async function loadAllCards() {
        try {
            const response = await fetch('/api/shanlian');
            if (response.ok) {
                const users = await response.json();
                console.log('Loaded all users:', users); // 输出数据

                // 清空现有的卡片
                cardsContainer.innerHTML = '';

                users.forEach(user => {
                    const card = createCard(user);
                    cardsContainer.appendChild(card);
                    console.log(`Generated card with data-category: ${card.getAttribute('data-category')}`); // 输出卡片数据
                });
            } else {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    async function filterCards(params) {
        try {
            const response = await fetch(`/filter_users?${params}`);
            if (response.ok) {
                const filteredUsers = await response.json();
                console.log('Filtered users:', filteredUsers); // 输出数据

                // 清空现有的卡片
                cardsContainer.innerHTML = '';

                filteredUsers.forEach(user => {
                    const card = createCard(user);
                    cardsContainer.appendChild(card);
                    console.log(`Generated card with data-category: ${card.getAttribute('data-category')}`); // 输出卡片数据
                });
            } else {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error filtering users:', error);
        }
    }

    function createCard(user) {
        //----
        console.log('Creating card for user:', user); // 检查 user 对象
        //---
        const categoryString = `${user.campus} ${user.grade} ${user.gender} ${user.college} `;

        const cardElement = document.createElement('div');
        cardElement.classList.add('card');
        cardElement.setAttribute('data-category', categoryString);

        cardElement.innerHTML = `
            <div class="front">
                <h5>${user.username}</h5>
            </div>
            <div class="back">
                <h5>About ${user.username}</h5>
                <h6>${user.gender}</h6>
                <p>${user.college}</p>
                <button class="add-to-chat" data-user-id="${user.id}">添加到对话</button>
            </div>
        `;

        // 添加点击事件，点击按钮时将用户添加到对话列表
        cardElement.querySelector('.add-to-chat').addEventListener('click', function () {
            const receiverId = this.getAttribute('data-user-id');
            console.log('Receiver ID:', receiverId);  // 调试输出 receiver_id
            addToChat(receiverId, currentUserId);
        });

        return cardElement;
    }


    async function addToChat(receiverId, currentUserId) {
        try {
            // 获取当前用户的 ID----------------------------------------------------
            //const senderId = currentUserId;

            // 调试输出 sender_id 和 receiver_id
            console.log('Sender ID:', currentUserId);
            console.log('Receiver ID:', receiverId);

            // 如果 sender_id 或 receiver_id 无效，弹出警告
            if (!currentUserId || currentUserId === 'undefined' || !receiverId || receiverId === 'undefined') {
                alert('发送者或接收者 ID 无效');
                return;
            }

            const response = await fetch('/add_to_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sender_id: currentUserId,
                    receiver_id: receiverId
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                alert('成功添加到对话列表');
                loadChattedUsers();  // 刷新对话列表
            } else {
                alert('添加到对话列表失败: ' + data.message);
            }
        } catch (error) {
            console.error('添加到对话时出错:', error);
        }
    }


    async function loadChattedUsers() {
        try {
            const response = await fetch('/get_chatted_users');
            if (response.ok) {
                const chattedUsers = await response.json();
                console.log('加载的对话用户:', chattedUsers);  // 查看返回的对话用户数据

                const chattedList = document.getElementById('chatted-list');
                chattedList.innerHTML = '';  // 清空当前对话列表

                chattedUsers.forEach(user => {
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

});
