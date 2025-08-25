/**
 * Система черновиков для методов принятия решений
 * Обеспечивает сохранение и загрузку прогресса работы пользователя
 */

class DraftsManager {
    constructor() {
        this.currentDraftId = null;
        this.autoSaveInterval = null;
        this.lastSavedData = null;
        this.init();
    }

    init() {
        // Проверяем, загружается ли страница из черновика
        this.checkForDraft();

        // Запускаем автосохранение
        this.startAutoSave();

        // Добавляем обработчик перед уходом со страницы
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));

        // Показываем кнопку сохранения на страницах методов
        this.showSaveButton();
    }

    /**
     * Проверяет, есть ли параметр draft в URL
     */
    checkForDraft() {
        const urlParams = new URLSearchParams(window.location.search);
        const draftId = urlParams.get('draft');

        if (draftId) {
            this.loadDraftData(draftId);
        }
    }

    /**
     * Загружает данные черновика
     */
    async loadDraftData(draftId) {
        try {
            const response = await fetch(`/drafts/api/${draftId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch draft');
            }

            const draft = await response.json();
            this.currentDraftId = draftId;

            // Восстанавливаем данные
            this.restoreFormData(draft.form_data);

            // Показываем уведомление
            this.showNotification('Чернетку завантажено', 'success');

        } catch (error) {
            console.error('Error loading draft:', error);
            this.showNotification('Помилка завантаження чернетки', 'error');
        }
    }

    /**
     * Восстанавливает данные форм из черновика
     */
    restoreFormData(formData) {
        if (!formData) return;

        // Восстанавливаем основные данные
        if (formData.task) {
            const taskInput = document.querySelector('input[name="task"], textarea[name="task"]');
            if (taskInput) {
                taskInput.value = formData.task;
            }
        }

        // Восстанавливаем количество альтернатив и критериев
        if (formData.numAlternatives) {
            const altInput = document.querySelector('input[name="num_alternatives"]');
            if (altInput) {
                altInput.value = formData.numAlternatives;
            }
        }

        if (formData.numCriteria) {
            const critInput = document.querySelector('input[name="num_criteria"]');
            if (critInput) {
                critInput.value = formData.numCriteria;
            }
        }

        // Восстанавливаем имена альтернатив
        if (formData.alternatives && Array.isArray(formData.alternatives)) {
            formData.alternatives.forEach((alt, index) => {
                if (alt && alt.trim() !== '') {
                    const altInput = document.querySelector(`input[name="name_alternatives"][data-index="${index}"]`);
                    if (altInput) {
                        altInput.value = alt;
                    }
                }
            });
        }

        // Восстанавливаем имена критериев
        if (formData.criteria && Array.isArray(formData.criteria)) {
            formData.criteria.forEach((crit, index) => {
                if (crit && crit.trim() !== '') {
                    const critInput = document.querySelector(`input[name="name_criteria"][data-index="${index}"]`);
                    if (critInput) {
                        critInput.value = crit;
                    }
                }
            });
        }

        // Восстанавливаем матрицы
        if (formData.matrices) {
            this.restoreMatrices(formData.matrices);
        }

        // Восстанавливаем другие данные
        if (formData.otherData) {
            this.restoreOtherData(formData.otherData);
        }
    }

    /**
     * Восстанавливает матрицы из черновика
     */
    restoreMatrices(matrices) {
        // Восстанавливаем матрицу критериев
        if (matrices.criteria) {
            this.restoreMatrix('criteria', matrices.criteria);
        }

        // Восстанавливаем матрицы альтернатив
        if (matrices.alternatives) {
            Object.keys(matrices.alternatives).forEach(criteriaKey => {
                this.restoreMatrix(`alternatives_${criteriaKey}`, matrices.alternatives[criteriaKey]);
            });
        }
    }

    /**
 * Восстанавливает конкретную матрицу
 */
    restoreMatrix(matrixType, matrixData) {
        const matrixContainer = document.querySelector(`[data-matrix="${matrixType}"]`);
        if (!matrixContainer || !matrixData) return;

        const size = matrixData.length;

        for (let i = 0; i < size; i++) {
            for (let j = 0; j < size; j++) {
                if (matrixData[i] && matrixData[i][j] !== undefined && matrixData[i][j] !== '') {
                    let input = null;

                    if (i < j) {
                        input = matrixContainer.querySelector(`#matrix_krit_up_${i}_${j}`);
                    } else if (i > j) {
                        input = matrixContainer.querySelector(`#matrix_krit_low_${i}_${j}`);
                    } else {
                        input = matrixContainer.querySelector(`#matrix_krit_diag_${i}_${j}`);
                    }

                    if (input) {
                        input.value = matrixData[i][j];

                        // Если это верхний треугольник, обновляем симметричный элемент
                        if (i < j && input.id.includes('matrix_krit_up_')) {
                            const symmetricInput = matrixContainer.querySelector(`#matrix_krit_low_${j}_${i}`);
                            if (symmetricInput) {
                                let value = matrixData[i][j];
                                if (value && !isNaN(parseFloat(value))) {
                                    if (value.includes('/')) {
                                        const fraction = value.split('/');
                                        if (fraction.length === 2 && fraction[0] === '1') {
                                            symmetricInput.value = fraction[1];
                                        }
                                    } else {
                                        const num = parseFloat(value);
                                        if (num !== 1) {
                                            symmetricInput.value = `1/${num}`;
                                        } else {
                                            symmetricInput.value = '1';
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    /**
     * Восстанавливает другие данные
     */
    restoreOtherData(otherData) {
        Object.keys(otherData).forEach(key => {
            const element = document.querySelector(`[name="${key}"], [data-field="${key}"]`);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = otherData[key];
                } else if (element.type === 'radio') {
                    const radio = document.querySelector(`input[name="${key}"][value="${otherData[key]}"]`);
                    if (radio) {
                        radio.checked = true;
                    }
                } else {
                    element.value = otherData[key] || '';
                }
            }
        });
    }

    /**
     * Собирает все данные форм для сохранения
     */
    gatherFormData() {
        const formData = {
            task: this.getFieldValue('task'),
            numAlternatives: this.getFieldValue('num_alternatives'),
            numCriteria: this.getFieldValue('num_criteria'),
            alternatives: this.getAlternativesNames(),
            criteria: this.getCriteriaNames(),
            matrices: this.gatherMatrices(),
            otherData: this.gatherOtherData(),
            timestamp: new Date().toISOString()
        };

        // Фильтруем пустые значения
        if (formData.alternatives) {
            formData.alternatives = formData.alternatives.filter(alt => alt && alt.trim() !== '');
        }
        if (formData.criteria) {
            formData.criteria = formData.criteria.filter(crit => crit && crit.trim() !== '');
        }

        return formData;
    }

    /**
     * Получает значение поля формы
     */
    getFieldValue(fieldName) {
        const element = document.querySelector(`[name="${fieldName}"]`);
        if (!element) return null;

        if (element.type === 'checkbox') {
            return element.checked;
        } else if (element.type === 'radio') {
            const checked = document.querySelector(`input[name="${fieldName}"]:checked`);
            return checked ? checked.value : null;
        } else {
            return element.value || null;
        }
    }

    /**
     * Собирает имена альтернатив
     */
    getAlternativesNames() {
        const inputs = document.querySelectorAll('input[name="name_alternatives"]');
        return Array.from(inputs).map(input => input.value || '');
    }

    /**
     * Собирает имена критериев
     */
    getCriteriaNames() {
        const inputs = document.querySelectorAll('input[name="name_criteria"]');
        return Array.from(inputs).map(input => input.value || '');
    }

    /**
     * Собирает данные матриц
     */
    gatherMatrices() {
        const matrices = {};

        // Собираем матрицу критериев
        const criteriaMatrix = this.gatherMatrix('criteria');
        if (criteriaMatrix) {
            matrices.criteria = criteriaMatrix;
        }

        // Собираем матрицы альтернатив
        const alternativesMatrices = this.gatherAlternativesMatrices();
        if (Object.keys(alternativesMatrices).length > 0) {
            matrices.alternatives = alternativesMatrices;
        }

        return matrices;
    }

    /**
 * Собирает конкретную матрицу
 */
    gatherMatrix(matrixType) {
        const matrixContainer = document.querySelector(`[data-matrix="${matrixType}"]`);
        if (!matrixContainer) return null;

        const inputs = matrixContainer.querySelectorAll('input[type="text"]');
        if (inputs.length === 0) return null;

        // Определяем размер матрицы по количеству строк
        const rows = matrixContainer.querySelectorAll('tbody tr');
        const size = rows.length;

        if (size === 0) return null;

        const matrix = [];
        for (let i = 0; i < size; i++) {
            matrix[i] = [];
            for (let j = 0; j < size; j++) {
                // Ищем соответствующий input
                let input = null;
                if (i < j) {
                    input = matrixContainer.querySelector(`#matrix_krit_up_${i}_${j}`);
                } else if (i > j) {
                    input = matrixContainer.querySelector(`#matrix_krit_low_${i}_${j}`);
                } else {
                    input = matrixContainer.querySelector(`#matrix_krit_diag_${i}_${j}`);
                }

                if (input) {
                    matrix[i][j] = input.value || '';
                } else {
                    matrix[i][j] = '';
                }
            }
        }

        return matrix;
    }

    /**
     * Собирает матрицы альтернатив
     */
    gatherAlternativesMatrices() {
        const matrices = {};
        const matrixContainers = document.querySelectorAll('[data-matrix^="alternatives_"]');

        matrixContainers.forEach(container => {
            const matrixType = container.dataset.matrix;
            const criteriaKey = matrixType.replace('alternatives_', '');
            const matrix = this.gatherMatrix(matrixType);

            if (matrix) {
                matrices[criteriaKey] = matrix;
            }
        });

        return matrices;
    }

    /**
 * Собирает другие данные форм
 */
    gatherOtherData() {
        const otherData = {};
        const otherInputs = document.querySelectorAll('input:not([name="task"]):not([name="num_alternatives"]):not([name="num_criteria"]):not([name="name_alternatives"]):not([name="name_criteria"]):not([name="matrix_krit"]), textarea:not([name="task"]), select');

        otherInputs.forEach(input => {
            if (input.name && input.name !== 'name_alternatives' && input.name !== 'name_criteria' && input.name !== 'matrix_krit') {
                if (input.type === 'checkbox') {
                    otherData[input.name] = input.checked;
                } else if (input.type === 'radio') {
                    const checked = document.querySelector(`input[name="${input.name}"]:checked`);
                    if (checked) {
                        otherData[input.name] = checked.value;
                    }
                } else {
                    otherData[input.name] = input.value || '';
                }
            }
        });

        return otherData;
    }

    /**
     * Сохраняет черновик
     */
    async saveDraft(title = null) {
        try {
            const formData = this.gatherFormData();

            // Проверяем, есть ли изменения
            if (this.lastSavedData && JSON.stringify(formData) === JSON.stringify(this.lastSavedData)) {
                this.showNotification('Немає змін для збереження', 'info');
                return;
            }

            const draftData = {
                method_type: this.getCurrentMethodType(),
                current_route: window.location.pathname,
                form_data: formData,
                title: title
            };

            const response = await fetch('/drafts/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(draftData)
            });

            if (!response.ok) {
                throw new Error('Failed to save draft');
            }

            const result = await response.json();
            this.currentDraftId = result.draft_id;
            this.lastSavedData = formData;

            this.showNotification('Чернетку збережено', 'success');

            // Обновляем URL если это новый черновик
            if (!window.location.search.includes('draft=')) {
                const newUrl = `${window.location.pathname}?draft=${this.currentDraftId}`;
                window.history.replaceState({}, '', newUrl);
            }

        } catch (error) {
            console.error('Error saving draft:', error);
            this.showNotification('Помилка збереження чернетки', 'error');
        }
    }

    /**
     * Определяет текущий тип метода
     */
    getCurrentMethodType() {
        const path = window.location.pathname;

        if (path.includes('/hierarchy')) return 'hierarchy';
        if (path.includes('/binary')) return 'binary';
        if (path.includes('/experts')) return 'experts';
        if (path.includes('/laplasa')) return 'laplasa';
        if (path.includes('/maximin')) return 'maximin';
        if (path.includes('/savage')) return 'savage';
        if (path.includes('/hurwitz')) return 'hurwitz';

        return 'unknown';
    }

    /**
     * Запускает автосохранение
     */
    startAutoSave() {
        // Автосохранение каждые 2 минуты
        this.autoSaveInterval = setInterval(() => {
            if (this.hasFormData()) {
                this.saveDraft();
            }
        }, 120000); // 2 минуты
    }

    /**
 * Проверяет, есть ли данные для сохранения
 */
    hasFormData() {
        const formData = this.gatherFormData();
        return formData.task ||
            (formData.alternatives && formData.alternatives.some(alt => alt && alt.trim() !== '')) ||
            (formData.criteria && formData.criteria.some(crit => crit && crit.trim() !== '')) ||
            (formData.matrices && Object.keys(formData.matrices).length > 0);
    }

    /**
     * Обрабатывает событие перед уходом со страницы
     */
    handleBeforeUnload(event) {
        if (this.hasUnsavedChanges()) {
            event.preventDefault();
            event.returnValue = 'У вас є незбережені зміни. Дійсно хочете покинути сторінку?';
            return event.returnValue;
        }
    }

    /**
     * Проверяет, есть ли несохраненные изменения
     */
    hasUnsavedChanges() {
        if (!this.lastSavedData) return this.hasFormData();

        const currentData = this.gatherFormData();
        return JSON.stringify(currentData) !== JSON.stringify(this.lastSavedData);
    }

    /**
     * Показывает уведомление
     */
    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `draft-notification draft-notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;

        // Добавляем в DOM
        document.body.appendChild(notification);

        // Обработчик закрытия
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });

        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Останавливает автосохранение
     */
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }

    /**
     * Показывает кнопку сохранения на страницах методов
     */
    showSaveButton() {
        const saveButton = document.getElementById('draft-save-button');
        if (!saveButton) return;

        // Показываем кнопку только на страницах методов
        const isMethodPage = this.getCurrentMethodType() !== 'unknown';

        if (isMethodPage) {
            saveButton.style.display = 'block';
        } else {
            saveButton.style.display = 'none';
        }
    }

    /**
     * Очищает данные черновика
     */
    clearDraft() {
        this.currentDraftId = null;
        this.lastSavedData = null;

        // Убираем параметр draft из URL
        const url = new URL(window.location);
        url.searchParams.delete('draft');
        window.history.replaceState({}, '', url);
    }
}

// Создаем глобальный экземпляр менеджера черновиков
window.draftsManager = new DraftsManager();

// Добавляем CSS для уведомлений
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .draft-notification .notification-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .draft-notification .notification-close {
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        margin-left: 15px;
        padding: 0;
        line-height: 1;
    }

    .draft-notification .notification-close:hover {
        opacity: 0.8;
    }
`;
document.head.appendChild(notificationStyles);
