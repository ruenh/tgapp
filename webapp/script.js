// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Получить параметры из URL
const urlParams = new URLSearchParams(window.location.search);
const drawId = urlParams.get('draw_id');

// Получить данные пользователя
const initData = tg.initDataUnsafe;
const user = initData.user;

// Экраны
const screens = {
    loading: document.getElementById('loading'),
    success: document.getElementById('success'),
    already: document.getElementById('already'),
    error: document.getElementById('error'),
    fatalError: document.getElementById('fatal-error')
};

// Показать экран
function showScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[screenName].classList.add('active');
}

// Проверка участия
async function checkParticipation() {
    if (!drawId) {
        showScreen('fatalError');
        document.getElementById('fatal-error-message').textContent = 'Неверная ссылка на розыгрыш';
        return;
    }
    
    if (!user) {
        showScreen('fatalError');
        document.getElementById('fatal-error-message').textContent = 'Не удалось получить данные пользователя';
        return;
    }
    
    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: user.id,
                first_name: user.first_name,
                username: user.username || null,
                draw_id: drawId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.already_participating) {
                showScreen('already');
            } else {
                showScreen('success');
                // Вибрация при успехе
                if (tg.HapticFeedback) {
                    tg.HapticFeedback.notificationOccurred('success');
                }
            }
        } else {
            showScreen('error');
            document.getElementById('error-message').textContent = data.message;
            
            // Показать список каналов
            if (data.missing_channels && data.missing_channels.length > 0) {
                const channelsList = document.getElementById('channels-list');
                channelsList.innerHTML = '<p style="margin-bottom: 10px; font-weight: 500;">Подпишитесь на:</p>';
                
                data.missing_channels.forEach(channel => {
                    const channelItem = document.createElement('div');
                    channelItem.className = 'channel-item';
                    channelItem.innerHTML = `
                        <span class="channel-name">${channel}</span>
                        <a href="https://t.me/${channel.replace('@', '')}" 
                           target="_blank" 
                           style="color: var(--tg-theme-link-color, #3390ec); text-decoration: none;">
                            Подписаться →
                        </a>
                    `;
                    channelsList.appendChild(channelItem);
                });
            }
            
            // Вибрация при ошибке
            if (tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('error');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showScreen('fatalError');
        document.getElementById('fatal-error-message').textContent = 
            'Произошла ошибка при проверке. Попробуйте позже.';
    }
}

// Кнопка повторной проверки
document.getElementById('retry-btn').addEventListener('click', () => {
    showScreen('loading');
    setTimeout(checkParticipation, 500);
});

// Запуск проверки при загрузке
checkParticipation();

// Закрытие Mini App по кнопке Back
tg.BackButton.onClick(() => {
    tg.close();
});
tg.BackButton.show();
