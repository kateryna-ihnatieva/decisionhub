/**
 * Обработчик навигации для предотвращения предупреждений при переходе между страницами
 */

class NavigationHandler {
    constructor() {
        this.init();
    }

    init() {
        // Помечаем все существующие ссылки как внутренние
        this.markAllLinks();

        // Наблюдаем за изменениями в DOM для новых ссылок
        this.observeDOMChanges();

        // Обрабатываем программную навигацию
        this.handleProgrammaticNavigation();
    }

    /**
     * Помечает все ссылки на странице как внутренние
     */
    markAllLinks() {
        // Помечаем все ссылки
        const allLinks = document.querySelectorAll('a[href]');
        allLinks.forEach(link => {
            this.markLinkAsInternal(link);
        });

        // Помечаем все кнопки, которые могут вести к навигации
        const allButtons = document.querySelectorAll('button, input[type="submit"]');
        allButtons.forEach(button => {
            this.markButtonAsInternal(button);
        });

        // Помечаем все формы
        const allForms = document.querySelectorAll('form');
        allForms.forEach(form => {
            this.markFormAsInternal(form);
        });
    }

    /**
     * Помечает ссылку как внутреннюю навигацию
     */
    markLinkAsInternal(link) {
        // Проверяем, что это не внешняя ссылка
        if (link.href && !this.isExternalLink(link.href)) {
            link.addEventListener('click', (event) => {
                sessionStorage.setItem('isInternalNavigation', 'true');
                console.log('Link clicked, marked as internal navigation:', link.href);
            });
        }
    }

    /**
     * Помечает кнопку как внутреннюю навигацию
     */
    markButtonAsInternal(button) {
        button.addEventListener('click', (event) => {
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Button clicked, marked as internal navigation:', button.textContent || button.type);
        });
    }

    /**
     * Помечает форму как внутреннюю навигацию
     */
    markFormAsInternal(form) {
        form.addEventListener('submit', (event) => {
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Form submitted, marked as internal navigation');
        });
    }

    /**
     * Проверяет, является ли ссылка внешней
     */
    isExternalLink(href) {
        try {
            const url = new URL(href);
            return url.hostname !== window.location.hostname;
        } catch (e) {
            return false;
        }
    }

    /**
     * Наблюдает за изменениями в DOM для новых элементов
     */
    observeDOMChanges() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Проверяем новые ссылки
                            const newLinks = node.querySelectorAll ? node.querySelectorAll('a[href]') : [];
                            newLinks.forEach(link => this.markLinkAsInternal(link));

                            // Проверяем новые кнопки
                            const newButtons = node.querySelectorAll ? node.querySelectorAll('button, input[type="submit"]') : [];
                            newButtons.forEach(button => this.markButtonAsInternal(button));

                            // Проверяем новые формы
                            const newForms = node.querySelectorAll ? node.querySelectorAll('form') : [];
                            newForms.forEach(form => this.markFormAsInternal(form));

                            // Если сам узел является ссылкой, кнопкой или формой
                            if (node.tagName === 'A' && node.href) {
                                this.markLinkAsInternal(node);
                            } else if (node.tagName === 'BUTTON' || node.type === 'submit') {
                                this.markButtonAsInternal(node);
                            } else if (node.tagName === 'FORM') {
                                this.markFormAsInternal(node);
                            }
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Обрабатывает программную навигацию
     */
    handleProgrammaticNavigation() {
        // Перехватываем history.pushState и history.replaceState
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = (...args) => {
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Programmatic navigation detected: pushState');
            return originalPushState.apply(history, args);
        };

        history.replaceState = (...args) => {
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Programmatic navigation detected: replaceState');
            return originalReplaceState.apply(history, args);
        };

        // Обрабатываем popstate (навигация назад/вперед)
        window.addEventListener('popstate', () => {
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Programmatic navigation detected: popstate');
        });
    }
}

// Создаем глобальный экземпляр обработчика навигации
window.navigationHandler = new NavigationHandler();

// Дополнительная обработка для всех ссылок на странице
document.addEventListener('click', (event) => {
    const target = event.target.closest('a, button, input[type="submit"]');

    if (target) {
        if (target.tagName === 'A' && target.href) {
            // Это ссылка
            if (!target.href.startsWith('javascript:') && !target.href.startsWith('#')) {
                // Проверяем, является ли это внутренней ссылкой
                try {
                    const url = new URL(target.href);
                    if (url.hostname === window.location.hostname || url.hostname === '') {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                        console.log('Global click handler: Internal link marked as internal navigation:', target.href);
                    }
                } catch (e) {
                    // Если не удается разобрать URL, считаем внутренней
                    sessionStorage.setItem('isInternalNavigation', 'true');
                    console.log('Global click handler: Link marked as internal navigation (fallback):', target.href);
                }
            }
        } else if (target.tagName === 'BUTTON' || target.type === 'submit') {
            // Это кнопка
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Global click handler: Button marked as internal navigation');
        }
    }
});

// Обработка всех форм
document.addEventListener('submit', (event) => {
    sessionStorage.setItem('isInternalNavigation', 'true');
    console.log('Global submit handler: Form marked as internal navigation');
});

console.log('NavigationHandler initialized');
