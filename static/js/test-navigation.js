/**
 * Тестовый файл для проверки работы системы навигации
 */

console.log('Test navigation script loaded');

// Функция для тестирования внутренней навигации
function testInternalNavigation() {
    console.log('Testing internal navigation...');

    // Проверяем текущее состояние
    const isInternal = sessionStorage.getItem('isInternalNavigation');
    console.log('Current isInternalNavigation state:', isInternal);

    // Симулируем клик по внутренней ссылке
    const testLink = document.createElement('a');
    testLink.href = '/test';
    testLink.click();

    // Проверяем состояние после клика
    setTimeout(() => {
        const newState = sessionStorage.getItem('isInternalNavigation');
        console.log('State after test click:', newState);
        console.log('Test completed');
    }, 100);
}

// Функция для тестирования beforeunload
function testBeforeUnload() {
    console.log('Testing beforeunload...');

    // Создаем тестовое событие
    const testEvent = new Event('beforeunload');

    // Вызываем обработчик
    if (window.draftsManager && window.draftsManager.handleBeforeUnload) {
        const result = window.draftsManager.handleBeforeUnload(testEvent);
        console.log('BeforeUnload test result:', result);
    } else {
        console.log('DraftsManager not available for testing');
    }
}

// Экспортируем функции для тестирования
window.testNavigation = {
    testInternalNavigation,
    testBeforeUnload
};

console.log('Test functions available at window.testNavigation');
