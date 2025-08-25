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
        // Очищаем старые данные черновика из sessionStorage при инициализации
        sessionStorage.removeItem('draft_form_data');

        // Проверяем, загружается ли страница из черновика
        this.checkForDraft();

        // Запускаем автосохранение
        this.startAutoSave();

        // Добавляем обработчик перед уходом со страницы
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));

        // Показываем кнопку сохранения на страницах методов
        this.showSaveButton();

        // Дополнительная проверка после полной загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.showSaveButton();
            });
        }

        // Обработчик изменения URL (для SPA)
        window.addEventListener('popstate', () => {
            setTimeout(() => this.showSaveButton(), 100);
        });

        // Обработчик изменения истории (для программной навигации)
        const originalPushState = history.pushState;
        history.pushState = function (...args) {
            originalPushState.apply(history, args);
            setTimeout(() => this.showSaveButton(), 100);
        }.bind(this);

        // Перехватываем клики по ссылкам и кнопкам навигации
        this.interceptNavigationClicks();

        // Периодическая проверка кнопки (каждые 2 секунды)
        setInterval(() => {
            this.showSaveButton();
        }, 2000);
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

        console.log('Restoring form data:', formData);

        // Восстанавливаем задачу (проверяем все возможные имена полей)
        if (formData.task) {
            const taskInput = document.querySelector('input[name="task"]') ||
                document.querySelector('textarea[name="task"]') ||
                document.querySelector('input[name="hierarchy_task"]') ||
                document.querySelector('textarea[name="hierarchy_task"]') ||
                document.querySelector('input[name="binary_task"]') ||
                document.querySelector('textarea[name="binary_task"]') ||
                document.querySelector('input[name="experts_task"]') ||
                document.querySelector('textarea[name="experts_task"]') ||
                document.querySelector('input[name="laplasa_task"]') ||
                document.querySelector('textarea[name="laplasa_task"]') ||
                document.querySelector('input[name="maximin_task"]') ||
                document.querySelector('textarea[name="maximin_task"]') ||
                document.querySelector('input[name="hurwitz_task"]') ||
                document.querySelector('textarea[name="hurwitz_task"]') ||
                document.querySelector('input[name="savage_task"]') ||
                document.querySelector('textarea[name="savage_task"]');
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
            console.log('Restoring alternatives:', formData.alternatives);
            formData.alternatives.forEach((alt, index) => {
                // Восстанавливаем все значения, включая пустые строки
                const altInput = document.querySelector(`input[name="name_alternatives"][data-index="${index}"]`);
                if (altInput) {
                    altInput.value = alt || '';
                    console.log(`Restored alternative[${index}]: "${alt}" -> "${altInput.value}"`);
                } else {
                    console.warn(`Alternative input not found for index ${index}`);
                }
            });
        }

        // Восстанавливаем имена критериев
        if (formData.criteria && Array.isArray(formData.criteria)) {
            console.log('Restoring criteria:', formData.criteria);
            formData.criteria.forEach((crit, index) => {
                // Восстанавливаем все значения, включая пустые строки
                const critInput = document.querySelector(`input[name="name_criteria"][data-index="${index}"]`);
                if (critInput) {
                    critInput.value = crit || '';
                    console.log(`Restored criteria[${index}]: "${crit}" -> "${critInput.value}"`);
                } else {
                    console.warn(`Criteria input not found for index ${index}`);
                }
            });
        }

        // Восстанавливаем имена условий (для Savage)
        if (formData.conditions && Array.isArray(formData.conditions)) {
            console.log('Restoring conditions:', formData.conditions);
            formData.conditions.forEach((cond, index) => {
                // Восстанавливаем все значения, включая пустые строки
                const condInput = document.querySelector(`input[name="name_conditions"][data-index="${index}"]`);
                if (condInput) {
                    condInput.value = cond || '';
                    console.log(`Restored condition[${index}]: "${cond}" -> "${condInput.value}"`);
                } else {
                    console.warn(`Condition input not found for index ${index}`);
                }
            });
        }

        // Восстанавливаем имена объектов (для Binary Relations)
        if (formData.objects && Array.isArray(formData.objects)) {
            console.log('Restoring objects:', formData.objects);
            formData.objects.forEach((obj, index) => {
                // Восстанавливаем все значения, включая пустые строки
                const objInput = document.querySelector(`input[name="names"][data-index="${index}"]`);
                if (objInput) {
                    objInput.value = obj || '';
                    console.log(`Restored object[${index}]: "${obj}" -> "${objInput.value}"`);
                } else {
                    console.warn(`Object input not found for index ${index}`);
                }
            });
        }

        // Восстанавливаем имена исследований (для Experts)
        if (formData.research && Array.isArray(formData.research)) {
            console.log('Restoring research:', formData.research);
            formData.research.forEach((res, index) => {
                // Восстанавливаем все значения, включая пустые строки
                const resInput = document.querySelector(`input[name="name_research"][data-index="${index}"]`);
                if (resInput) {
                    resInput.value = res || '';
                    console.log(`Restored research[${index}]: "${res}" -> "${resInput.value}"`);
                } else {
                    console.warn(`Research input not found for index ${index}`);
                }
            });
        }

        // Восстанавливаем матрицы
        if (formData.matrices) {
            this.restoreMatrices(formData.matrices);
        }

        // Восстанавливаем другие данные (только если основные данные не были восстановлены)
        if (formData.otherData) {
            this.restoreOtherData(formData.otherData);
        }

        // Принудительно обновляем форму после восстановления числовых значений
        this.forceFormUpdate();

        // Сохраняем восстановленные данные в sessionStorage для использования при повторном сохранении
        try {
            // Правильно обрабатываем Unicode символы
            const cleanFormData = JSON.parse(JSON.stringify(formData));
            sessionStorage.setItem('draft_form_data', JSON.stringify(cleanFormData));
        } catch (e) {
            console.error('Error saving draft data to sessionStorage:', e);
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
        console.log('Restoring other data:', otherData);

        Object.keys(otherData).forEach(key => {
            // Проверяем, не является ли это полем, которое уже было восстановлено из основного черновика
            if (key === 'name_alternatives' || key === 'name_criteria' || key === 'name_conditions' || key === 'names' || key === 'name_research') {
                console.log(`Skipping ${key} as it's already restored from main draft data`);
                return; // Пропускаем эти поля, так как они уже восстановлены
            }

            const element = document.querySelector(`[name="${key}"], [data-field="${key}"]`);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = otherData[key];
                    console.log(`Restored checkbox ${key}: ${otherData[key]}`);
                } else if (element.type === 'radio') {
                    const radio = document.querySelector(`input[name="${key}"][value="${otherData[key]}"]`);
                    if (radio) {
                        radio.checked = true;
                        console.log(`Restored radio ${key}: ${otherData[key]}`);
                    }
                } else {
                    element.value = otherData[key] || '';
                    console.log(`Restored input ${key}: "${otherData[key]}" -> "${element.value}"`);
                }
            } else {
                console.warn(`Element not found for ${key}`);
            }
        });
    }

    /**
     * Собирает все данные форм для сохранения
     */
    gatherFormData() {
        // Собираем данные со всех возможных источников
        const formData = {
            task: this.getFieldValue('task') || this.getFieldValue('hierarchy_task') || this.getFieldValue('binary_task') || this.getFieldValue('experts_task') || this.getFieldValue('laplasa_task') || this.getFieldValue('maximin_task') || this.getFieldValue('hurwitz_task') || this.getFieldValue('savage_task') || this.getFieldValue('savage_task'),
            numAlternatives: this.getFieldValue('num_alternatives') || this.getFieldValue('num_alt') || this.getUrlParam('num_alternatives') || this.getUrlParam('num_alt') || 0,
            numCriteria: this.getFieldValue('num_criteria') || this.getUrlParam('num_criteria') || 0,
            numConditions: this.getFieldValue('num_conditions') || this.getUrlParam('num_conditions') || 0,
            numObjects: this.getFieldValue('num') || this.getUrlParam('num') || 0,
            numExperts: this.getFieldValue('num_experts') || this.getUrlParam('num_experts') || 0,
            numResearch: this.getFieldValue('num_research') || this.getUrlParam('num_research') || 0,
            alternatives: this.getAlternativesNames(),
            criteria: this.getCriteriaNames(),
            conditions: this.getConditionsNames(),
            objects: this.getObjectsNames(),
            research: this.getResearchNames(),
            alpha: this.getFieldValue('alpha') || this.getUrlParam('alpha') || 0.5,
            matrixType: this.getFieldValue('matrix_type') || this.getUrlParam('matrix_type'),
            matrices: this.gatherMatrices(),
            otherData: this.gatherOtherData(),
            timestamp: new Date().toISOString()
        };

        // Всегда пытаемся получить дополнительные данные из sessionStorage (восстановленные данные)
        const restoredData = sessionStorage.getItem('draft_form_data');
        if (restoredData) {
            try {
                const parsed = JSON.parse(restoredData);

                // Используем восстановленные данные как fallback для числовых полей
                if (!formData.numAlternatives || formData.numAlternatives === 0) {
                    formData.numAlternatives = parsed.numAlternatives || 0;
                }
                if (!formData.numCriteria || formData.numCriteria === 0) {
                    formData.numCriteria = parsed.numCriteria || 0;
                }
                if (!formData.numConditions || formData.numConditions === 0) {
                    formData.numConditions = parsed.numConditions || 0;
                }
                if (!formData.numObjects || formData.numObjects === 0) {
                    formData.numObjects = parsed.numObjects || 0;
                }
                if (!formData.numExperts || formData.numExperts === 0) {
                    formData.numExperts = parsed.numExperts || 0;
                }
                if (!formData.numResearch || formData.numResearch === 0) {
                    formData.numResearch = parsed.numResearch || 0;
                }

                // Используем восстановленные данные как fallback для имен, если текущие пусты
                if (!formData.alternatives || formData.alternatives.length === 0 || formData.alternatives.every(alt => !alt || alt.trim() === '')) {
                    formData.alternatives = parsed.alternatives || [];
                }
                if (!formData.criteria || formData.criteria.length === 0 || formData.criteria.every(crit => !crit || crit.trim() === '')) {
                    formData.criteria = parsed.criteria || [];
                }
                if (!formData.conditions || formData.conditions.length === 0 || formData.conditions.every(cond => !cond || cond.trim() === '')) {
                    formData.conditions = parsed.conditions || [];
                }
                if (!formData.objects || formData.objects.length === 0 || formData.objects.every(obj => !obj || obj.trim() === '')) {
                    formData.objects = parsed.objects || [];
                }
                if (!formData.research || formData.research.length === 0 || formData.research.every(res => !res || res.trim() === '')) {
                    formData.research = parsed.research || [];
                }

                // Используем восстановленную задачу, если текущая пуста
                if (!formData.task || formData.task.trim() === '') {
                    formData.task = parsed.task || null;
                }

                // Используем восстановленные матрицы, если текущие пусты
                if (!formData.matrices || Object.keys(formData.matrices).length === 0) {
                    formData.matrices = parsed.matrices || {};
                }

            } catch (e) {
                console.error('Error parsing restored draft data:', e);
            }
        }

        // НЕ фильтруем пустые значения - сохраняем все как есть, включая пустые строки
        // Это позволяет сохранить точную структуру введенных данных

        // Отладочная информация для проверки собранных данных
        console.log('Gathered form data:', formData);
        console.log('Alternatives:', formData.alternatives);
        console.log('Conditions:', formData.conditions);
        console.log('Task:', formData.task);
        console.log('NumAlternatives:', formData.numAlternatives);
        console.log('NumConditions:', formData.numConditions);

        // Дополнительная отладочная информация
        console.log('Form inputs found:');
        console.log('- name_alternatives:', document.querySelectorAll('input[name="name_alternatives"]').length);
        console.log('- name_conditions:', document.querySelectorAll('input[name="name_conditions"]').length);
        console.log('- savage_task:', document.querySelector('textarea[name="savage_task"]') ? 'found' : 'not found');

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
        const names = new Array(inputs.length);

        inputs.forEach(input => {
            const index = input.getAttribute('data-index');
            if (index !== null) {
                const idx = parseInt(index);
                if (!isNaN(idx) && idx >= 0 && idx < names.length) {
                    names[idx] = input.value || '';
                }
            }
        });

        return names;
    }

    /**
     * Собирает имена критериев
     */
    getCriteriaNames() {
        const inputs = document.querySelectorAll('input[name="name_criteria"]');
        const names = new Array(inputs.length);

        inputs.forEach(input => {
            const index = input.getAttribute('data-index');
            if (index !== null) {
                const idx = parseInt(index);
                if (!isNaN(idx) && idx >= 0 && idx < names.length) {
                    names[idx] = input.value || '';
                }
            }
        });

        return names;
    }

    /**
     * Собирает имена условий (для Savage)
     */
    getConditionsNames() {
        const inputs = document.querySelectorAll('input[name="name_conditions"]');
        const names = new Array(inputs.length);

        inputs.forEach(input => {
            const index = input.getAttribute('data-index');
            if (index !== null) {
                const idx = parseInt(index);
                if (!isNaN(idx) && idx >= 0 && idx < names.length) {
                    names[idx] = names[idx] || input.value || '';
                }
            }
        });

        return names;
    }

    /**
     * Собирает имена объектов (для Binary Relations)
     */
    getObjectsNames() {
        const inputs = document.querySelectorAll('input[name="names"]');
        const names = new Array(inputs.length);

        inputs.forEach(input => {
            const index = input.getAttribute('data-index');
            if (index !== null) {
                const idx = parseInt(index);
                if (!isNaN(idx) && idx >= 0 && idx < names.length) {
                    names[idx] = input.value || '';
                }
            }
        });

        return names;
    }

    /**
     * Собирает имена исследований (для Experts)
     */
    getResearchNames() {
        const inputs = document.querySelectorAll('input[name="name_research"]');
        const names = new Array(inputs.length);

        inputs.forEach(input => {
            const index = input.getAttribute('data-index');
            if (index !== null) {
                const idx = parseInt(index);
                if (!isNaN(idx) && idx >= 0 && idx < names.length) {
                    names[idx] = input.value || '';
                }
            }
        });

        return names;
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
        console.log('Checking path:', path);

        // Проверяем точные совпадения для основных страниц методов
        if (path === '/hierarchy' || path.startsWith('/hierarchy/')) return 'hierarchy';
        if (path === '/binary' || path.startsWith('/binary/')) return 'binary';
        if (path === '/experts' || path.startsWith('/experts/')) return 'experts';
        if (path === '/laplasa' || path.startsWith('/laplasa/')) return 'laplasa';
        if (path === '/maximin' || path.startsWith('/maximin/')) return 'maximin';
        if (path === '/savage' || path.startsWith('/savage/')) return 'savage';
        if (path === '/hurwitz' || path.startsWith('/hurwitz/')) return 'hurwitz';

        console.log('No method found, returning unknown');
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
            (formData.numAlternatives && formData.numAlternatives > 0) ||
            (formData.numCriteria && formData.numCriteria > 0) ||
            (formData.numConditions && formData.numConditions > 0) ||
            (formData.numObjects && formData.numObjects > 0) ||
            (formData.numExperts && formData.numExperts > 0) ||
            (formData.numResearch && formData.numResearch > 0) ||
            (formData.alternatives && formData.alternatives.some(alt => alt && alt.trim() !== '')) ||
            (formData.criteria && formData.criteria.some(crit => crit && crit.trim() !== '')) ||
            (formData.conditions && formData.conditions.some(cond => cond && cond.trim() !== '')) ||
            (formData.objects && formData.objects.some(obj => obj && obj.trim() !== '')) ||
            (formData.research && formData.research.some(res => res && res.trim() !== '')) ||
            (formData.matrices && Object.keys(formData.matrices).length > 0);
    }

    /**
     * Перехватывает клики по ссылкам и кнопкам навигации
     */
    interceptNavigationClicks() {
        // Перехватываем клики по ссылкам и кнопкам
        document.addEventListener('click', (event) => {
            const target = event.target.closest('a, button, input[type="submit"]');

            if (target) {
                // Проверяем, является ли это навигацией
                if (target.tagName === 'A' && target.href && !target.href.startsWith('javascript:') && !target.href.startsWith('#')) {
                    // Это ссылка на другую страницу
                    sessionStorage.setItem('isInternalNavigation', 'true');
                } else if (target.tagName === 'BUTTON' || target.type === 'submit') {
                    // Это кнопка, которая может вести к навигации
                    const form = target.closest('form');
                    if (form) {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                    }

                    // Проверяем текст кнопки на наличие слов навигации
                    const buttonText = target.textContent.toLowerCase();
                    if (buttonText.includes('далі') || buttonText.includes('дальше') ||
                        buttonText.includes('next') || buttonText.includes('продовжити') ||
                        buttonText.includes('continue') || buttonText.includes('вперед') ||
                        buttonText.includes('submit') || buttonText.includes('відправити') ||
                        buttonText.includes('завершити') || buttonText.includes('finish')) {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                    }

                    // Проверяем атрибуты кнопки
                    const buttonType = target.getAttribute('type');
                    if (buttonType === 'submit') {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                    }
                }
            }
        });

        // Перехватываем отправку форм
        document.addEventListener('submit', (event) => {
            // Все формы считаем внутренней навигацией
            sessionStorage.setItem('isInternalNavigation', 'true');
        });
    }

    /**
     * Обрабатывает событие перед уходом со страницы
     */
    handleBeforeUnload(event) {
        // Проверяем, является ли это навигацией внутри приложения
        const isInternalNavigation = sessionStorage.getItem('isInternalNavigation');

        if (isInternalNavigation === 'true') {
            // Это навигация внутри приложения, не показываем предупреждение
            sessionStorage.removeItem('isInternalNavigation');
            return;
        }

        // Проверяем, есть ли несохраненные изменения
        if (this.hasUnsavedChanges()) {
            // Показываем предупреждение только если есть реальные изменения
            event.preventDefault();
            event.returnValue = 'У вас є незбережені зміни. Дійсно хочете покинути сторінку?';
            return event.returnValue;
        }

        // Если нет изменений, не показываем предупреждение
        return;
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

        // Правильно обрабатываем Unicode символы в сообщении
        const cleanMessage = message.replace(/\\u[\dA-F]{4}/gi, (match) => {
            return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
        });

        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${cleanMessage}</span>
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
        if (!saveButton) {
            console.error('Save button not found');
            return;
        }

        // Показываем кнопку только на страницах методов
        const methodType = this.getCurrentMethodType();
        const isMethodPage = methodType !== 'unknown';

        console.log('Current path:', window.location.pathname);
        console.log('Method type:', methodType);
        console.log('Is method page:', isMethodPage);

        // Показываем кнопку на всех страницах методов
        if (isMethodPage) {
            saveButton.style.display = 'block';
            console.log('Save button shown');
        } else {
            saveButton.style.display = 'none';
            console.log('Save button hidden');
        }
    }

    /**
     * Принудительно обновляет форму после изменения числовых значений
     */
    forceFormUpdate() {
        // Находим все числовые поля и вызываем событие change
        const numericInputs = document.querySelectorAll('input[name="num_alternatives"], input[name="num_criteria"], input[name="num_conditions"], input[name="num"], input[name="num_experts"], input[name="num_research"], input[name="num_alt"]');

        numericInputs.forEach(input => {
            if (input.value && input.value > 0) {
                // Создаем событие change для обновления формы
                const event = new Event('change', { bubbles: true });
                input.dispatchEvent(event);
            }
        });
    }

    /**
     * Получает значение параметра из URL
     */
    getUrlParam(paramName) {
        const urlParams = new URLSearchParams(window.location.search);
        const value = urlParams.get(paramName);
        return value ? parseInt(value) || value : null;
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

// Отладочная информация
console.log('DraftsManager initialized');
console.log('Current path:', window.location.pathname);
console.log('Save button element:', document.getElementById('draft-save-button'));

// Дополнительная проверка
if (window.draftsManager) {
    console.log('DraftsManager created successfully');
    // Инициализируем после загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.draftsManager.init();
            window.draftsManager.showSaveButton();
        });
    } else {
        window.draftsManager.init();
        window.draftsManager.showSaveButton();
    }
} else {
    console.error('Failed to create DraftsManager');
}

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
