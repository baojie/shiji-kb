// ===== 游戏配置 =====
const GAME_CONFIG = {
    soundEnabled: true,
    musicEnabled: true
};

// ===== 音效系统 =====
const SOUNDS = {
    click: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju',
    success: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju',
    battle: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju',
    victory: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju',
    fire: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju',
    imperial: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju',
    ending: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIF2m98OScTgwOUKXh8LljHAU2jdXzzn0vBSh+zPLaizsKElyx6OyrWBUIQ5zd8sFuJAUuhM/y2Ik2CBdpvfDknE4MDlCl4fC5YxwFNo3V8859LwUofszy2os7ChJcseju'
};

function playSound(soundName) {
    if (!GAME_CONFIG.soundEnabled) return;
    try {
        const audio = new Audio(SOUNDS[soundName] || SOUNDS.click);
        audio.volume = 0.3;
        audio.play().catch(e => console.log('Sound play failed:', e));
    } catch (e) {
        console.log('Sound error:', e);
    }
}

// 由于篇幅限制，我将创建一个更新说明文档
