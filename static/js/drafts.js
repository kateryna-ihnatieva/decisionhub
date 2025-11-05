/**
 * Система черновиков для методов принятия решений
 * Обеспечивает сохранение и загрузку прогресса работы пользователя
 */

class DraftsManager {
    constructor() {
        this.currentDraftId = null;
        this.autoSaveInterval = null;
        this.lastSavedData = null;
        this.isAutoSaving = false;
        this.init();
    }

    init() {
        // Очищаем старые данные черновика из sessionStorage при инициализации
        sessionStorage.removeItem('draft_form_data');

        // Проверяем, загружается ли страница из черновика
        this.checkForDraft();

        // Запускаем автосохранение только на страницах методов (не на страницах с результатами)
        console.log('🚀 Initializing DraftsManager...');
        console.log('Is result page:', this.isResultPage());
        if (!this.isResultPage()) {
            console.log('✅ Starting auto-save (not a result page)');
            this.startAutoSave();
        } else {
            console.log('❌ Skipping auto-save (result page)');
        }

        // Добавляем обработчик перед уходом со страницы
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));

        // Показываем кнопку сохранения на страницах методов (но не на страницах с результатами)
        this.showSaveButton();

        // Дополнительная проверка: если это страница с результатами, сразу скрываем кнопку
        if (this.isResultPage()) {
            const saveButton = document.getElementById('draft-save-button');
            if (saveButton) {
                saveButton.style.display = 'none';
                console.log('Save button immediately hidden - result page detected');
            }
        }

        // Дополнительная отладочная информация
        console.log('DraftsManager init completed');
        console.log('Current path:', window.location.pathname);
        console.log('Method type:', this.getCurrentMethodType());
        console.log('Is result page:', this.isResultPage());
        console.log('Save button found:', !!document.getElementById('draft-save-button'));

        // Дополнительная проверка после полной загрузки DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.showSaveButton();
                this.markAllPageLinks();

                // Дополнительная проверка для страниц с результатами после загрузки DOM
                if (this.isResultPage()) {
                    const saveButton = document.getElementById('draft-save-button');
                    if (saveButton) {
                        saveButton.style.display = 'none';
                        console.log('Save button hidden after DOM load - result page detected');
                    }
                }
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

            // Дополнительная проверка для страниц с результатами
            if (this.isResultPage()) {
                const saveButton = document.getElementById('draft-save-button');
                if (saveButton) {
                    saveButton.style.display = 'none';
                    console.log('Save button hidden in periodic check - result page detected');
                }
            }
        }, 2000);

        // Дополнительная проверка для всех ссылок на странице
        this.markAllPageLinks();
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
            const altInput = document.querySelector('input[name="num_alternatives"]') || document.querySelector('input[name="num_alt"]');
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

        if (formData.numConditions) {
            const condInput = document.querySelector('input[name="num_conditions"]');
            if (condInput) {
                condInput.value = formData.numConditions;
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

        // Восстанавливаем данные матрицы критериев на странице матрицы альтернатив
        if (formData.matrices && formData.matrices.criteria) {
            this.restoreCriteriaMatrixOnAlternativesPage(formData.matrices.criteria);
        }

        // Восстанавливаем матрицу бинарных отношений
        if (formData.matrices && formData.matrices.binary) {
            this.restoreBinaryMatrix(formData.matrices.binary);
        }

        // Восстанавливаем матрицу компетенции экспертов
        if (formData.matrices && formData.matrices.competence) {
            this.restoreCompetenceMatrix(formData.matrices.competence);
        }

        // Восстанавливаем матрицу экспертных данных
        if (formData.matrices && formData.matrices.expertsData) {
            console.log('Restoring experts data matrix:', formData.matrices.expertsData);
            this.restoreExpertsDataMatrix(formData.matrices.expertsData);
        }

        // Восстанавливаем матрицу Лапласа (только если есть соответствующий контейнер)
        const laplasaContainer = document.querySelector('[data-matrix="laplasa"]');
        if (laplasaContainer && formData.matrices && formData.matrices.cost) {
            console.log('Restoring Laplasa matrix:', formData.matrices.cost);
            this.restoreLaplasaMatrix(formData.matrices.cost);
        }

        // Восстанавливаем матрицу максимина (только если есть соответствующий контейнер)
        const maximinContainer = document.querySelector('[data-matrix="maximin"]');
        if (maximinContainer && formData.matrices && formData.matrices.maximin) {
            console.log('Restoring Maximin matrix:', formData.matrices.maximin);
            this.restoreMaximinMatrix(formData.matrices.maximin);
        }

        // Восстанавливаем матрицу Севіджа (только если есть соответствующий контейнер)
        const savageContainer = document.querySelector('[data-matrix="savage"]');
        if (savageContainer && formData.matrices && formData.matrices.savage) {
            console.log('Restoring Savage matrix:', formData.matrices.savage);
            this.restoreSavageMatrix(formData.matrices.savage);
        }

        // Восстанавливаем матрицу Гурвица (только если есть соответствующий контейнер)
        const hurwitzContainer = document.querySelector('[data-matrix="hurwitz"]');
        if (hurwitzContainer && formData.matrices && formData.matrices.hurwitz) {
            console.log('Restoring Hurwitz matrix:', formData.matrices.hurwitz);
            this.restoreHurwitzMatrix(formData.matrices.hurwitz);
        }

        // Восстанавливаем тип матрицы
        if (formData.matrixType) {
            const matrixTypeInput = document.querySelector('input[name="matrix_type"][value="' + formData.matrixType + '"]');
            if (matrixTypeInput) {
                matrixTypeInput.checked = true;
                console.log('Restored matrix type:', formData.matrixType);
            }
        }

        // Восстанавливаем другие данные (только если основные данные не были восстановлены)
        if (formData.otherData) {
            console.log('=== RESTORING OTHER DATA ===');
            console.log('Other data:', formData.otherData);
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

        // Восстанавливаем матрицу бинарных отношений
        if (matrices.binary) {
            this.restoreBinaryMatrix(matrices.binary);
        }

        // Восстанавливаем матрицу компетенции экспертов
        if (matrices.competence) {
            this.restoreCompetenceMatrix(matrices.competence);
        }

        // Восстанавливаем матрицу экспертных данных
        if (matrices.expertsData) {
            this.restoreExpertsDataMatrix(matrices.expertsData);
        }
    }

    /**
    * Восстанавливает конкретную матрицу
    */
    restoreMatrix(matrixType, matrixData) {
        console.log(`Restoring matrix: ${matrixType}`, matrixData);
        const matrixContainer = document.querySelector(`[data-matrix="${matrixType}"]`);
        if (!matrixContainer || !matrixData) {
            console.log(`Matrix container not found or no data for: ${matrixType}`);
            return;
        }

        const size = matrixData.length;
        console.log(`Matrix size: ${size}`);

        for (let i = 0; i < size; i++) {
            for (let j = 0; j < size; j++) {
                if (matrixData[i] && matrixData[i][j] !== undefined && matrixData[i][j] !== '') {
                    let input = null;

                    if (matrixType.startsWith('alternatives_')) {
                        // Для матриц альтернатив используем новые имена полей
                        const criteriaNum = matrixType.replace('alternatives_', '');
                        input = matrixContainer.querySelector(`[name="matrix_alt_${criteriaNum}_${i}_${j}"]`);

                        if (input) {
                            console.log(`Found alternatives input for ${criteriaNum}_${i}_${j}:`, input);
                            // Устанавливаем значение
                            input.value = matrixData[i][j] || '';

                            // Обновляем симметричные элементы
                            if (i < j) {
                                const symmetricInput = matrixContainer.querySelector(`[name="matrix_alt_${criteriaNum}_${j}_${i}"]`);
                                if (symmetricInput) {
                                    let value = matrixData[i][j];
                                    if (value && value.trim() !== '') {
                                        if (value.includes('/')) {
                                            // Обработка дробей типа 1/3 → обратное значение 3
                                            const fraction = value.split('/');
                                            if (fraction.length === 2 && fraction[0] === '1') {
                                                symmetricInput.value = fraction[1];
                                                console.log(`Set symmetric value for ${criteriaNum}_${j}_${i}: ${fraction[1]}`);
                                            }
                                        } else {
                                            // Обработка целых чисел → обратное значение 1/число
                                            const num = parseFloat(value);
                                            if (num !== 1) {
                                                symmetricInput.value = `1/${num}`;
                                                console.log(`Set symmetric value for ${criteriaNum}_${j}_${i}: 1/${num}`);
                                            } else {
                                                symmetricInput.value = '1';
                                                console.log(`Set symmetric value for ${criteriaNum}_${j}_${i}: 1`);
                                            }
                                        }
                                    }
                                }
                            }
                        } else {
                            console.warn(`Alternatives input not found for ${criteriaNum}_${i}_${j}`);
                        }
                    } else if (matrixType === 'criteria') {
                        // Для матрицы критериев используем скрытые поля с name="matrix_krit"
                        // Создаем матрицу из скрытых полей
                        const inputs = matrixContainer.querySelectorAll('input[name="matrix_krit"]');
                        if (inputs.length === size * size) {
                            // Сортируем поля по порядку (i, j)
                            const sortedInputs = [];
                            for (let row = 0; row < size; row++) {
                                for (let col = 0; col < size; col++) {
                                    const inputIndex = row * size + col;
                                    if (inputs[inputIndex]) {
                                        sortedInputs.push(inputs[inputIndex]);
                                    }
                                }
                            }
                            const inputIndex = i * size + j;
                            if (sortedInputs[inputIndex]) {
                                input = sortedInputs[inputIndex];
                                input.value = matrixData[i][j] || '';
                                console.log(`Set criteria value for ${i}_${j}: ${matrixData[i][j]}`);
                            }
                        }
                    } else {
                        // Для других матриц используем старые имена (fallback)
                        if (i < j) {
                            input = matrixContainer.querySelector(`#matrix_krit_up_${i}_${j}`);
                        } else if (i > j) {
                            input = matrixContainer.querySelector(`#matrix_krit_low_${i}_${j}`);
                        } else {
                            input = matrixContainer.querySelector(`#matrix_krit_diag_${i}_${j}`);
                        }

                        if (input) {
                            input.value = matrixData[i][j] || '';
                            console.log(`Set fallback value for ${i}_${j}: ${matrixData[i][j]}`);
                        }
                    }
                }
            }
        }

        console.log(`Matrix ${matrixType} restored successfully`);
    }

    /**
     * Восстанавливает матрицу бинарных отношений
     */
    restoreBinaryMatrix(matrixData) {
        const matrixContainer = document.querySelector('[data-matrix="binary"]');
        if (!matrixContainer) {
            console.warn('Binary matrix container not found for restoration.');
            return;
        }

        const size = matrixData.length;
        if (size === 0) {
            console.warn('Matrix data for binary relations is empty.');
            return;
        }

        console.log('Restoring binary matrix with size:', size);
        console.log('Matrix data:', matrixData);

        // Восстанавливаем матрицу бинарных отношений
        const inputs = matrixContainer.querySelectorAll('input[name="matrix_binary"]');
        console.log('Found matrix inputs:', inputs.length);

        if (inputs.length === size * size) {
            for (let i = 0; i < size; i++) {
                for (let j = 0; j < size; j++) {
                    if (matrixData[i] && matrixData[i][j] !== undefined && matrixData[i][j] !== '') {
                        const inputIndex = i * size + j;
                        if (inputs[inputIndex]) {
                            inputs[inputIndex].value = matrixData[i][j] || '';
                            console.log(`Set binary relation value for ${i}_${j}: ${matrixData[i][j]}`);
                        } else {
                            console.warn(`Binary relation input not found for ${i}_${j}.`);
                        }
                    }
                }
            }
        } else {
            console.warn(`Expected ${size * size} inputs, but found ${inputs.length}`);

            // Fallback: попробуем восстановить по ID полей
            for (let i = 0; i < size; i++) {
                for (let j = 0; j < size; j++) {
                    if (matrixData[i] && matrixData[i][j] !== undefined && matrixData[i][j] !== '') {
                        let input = null;
                        if (i < j) {
                            input = matrixContainer.querySelector(`#matrix\\[${i}\\]\\[${j}\\]`);
                        } else if (i > j) {
                            input = matrixContainer.querySelector(`#matrix\\[${j}\\]\\[${i}\\]`);
                        } else {
                            input = matrixContainer.querySelector(`#matrix\\[${i}\\]\\[${j}\\]`);
                        }

                        if (input) {
                            input.value = matrixData[i][j] || '';
                            console.log(`Set binary relation value for ${i}_${j} via ID: ${matrixData[i][j]}`);
                        } else {
                            console.warn(`Binary relation input not found for ${i}_${j} via ID.`);
                        }
                    }
                }
            }
        }
    }

    /**
     * Восстанавливает матрицу компетенции экспертов
     */
    restoreCompetenceMatrix(matrixData) {
        const matrixContainer = document.querySelector('[data-matrix="competence"]');
        if (!matrixContainer) {
            console.warn('Competence matrix container not found for restoration.');
            return;
        }

        const numExperts = matrixData.length;
        if (numExperts === 0) {
            console.warn('Matrix data for competence is empty.');
            return;
        }

        const numArguments = matrixData[0] ? matrixData[0].length : 0;
        console.log('Restoring competence matrix with size:', numExperts, 'x', numArguments);
        console.log('Matrix data:', matrixData);

        // Восстанавливаем матрицу компетенции по ID полей
        for (let i = 0; i < numExperts; i++) {
            for (let j = 0; j < numArguments; j++) {
                // Проверяем, есть ли значение в матрице
                if (matrixData[i] && matrixData[i][j] !== undefined && matrixData[i][j] !== '' && matrixData[i][j] !== null) {
                    const input = matrixContainer.querySelector(`#table_competence_${j}_${i}`);
                    if (input) {
                        input.value = matrixData[i][j];
                        console.log(`Set competence value for expert ${i}, argument ${j}: ${matrixData[i][j]}`);
                    } else {
                        console.warn(`Competence input not found for expert ${i}, argument ${j}`);
                    }
                } else {
                    // Если значение пустое, очищаем поле
                    const input = matrixContainer.querySelector(`#table_competence_${j}_${i}`);
                    if (input) {
                        input.value = '';
                        console.log(`Cleared competence value for expert ${i}, argument ${j}`);
                    }
                }
            }
        }
    }

    /**
     * Восстанавливает матрицу экспертных данных
     */
    restoreExpertsDataMatrix(matrixData) {
        const matrixContainer = document.querySelector('[data-matrix="experts_data"]');
        if (!matrixContainer) {
            console.warn('Experts data matrix container not found for restoration.');
            return;
        }

        const numExperts = matrixData.length;
        if (numExperts === 0) {
            console.warn('Matrix data for experts data is empty.');
            return;
        }

        const numResearch = matrixData[0] ? matrixData[0].length : 0;
        console.log('Restoring experts data matrix with size:', numExperts, 'x', numResearch);
        console.log('Matrix data:', matrixData);

        // Восстанавливаем матрицу экспертных данных по ID полей
        for (let i = 0; i < numExperts; i++) {
            for (let j = 0; j < numResearch; j++) {
                // Проверяем, есть ли значение в матрице
                if (matrixData[i] && matrixData[i][j] !== undefined && matrixData[i][j] !== '' && matrixData[i][j] !== null) {
                    const input = matrixContainer.querySelector(`#experts_data_table_${j}_${i}`);
                    if (input) {
                        input.value = matrixData[i][j];
                        console.log(`Set experts data value for expert ${i}, research ${j}: ${matrixData[i][j]}`);
                    } else {
                        console.warn(`Experts data input not found for expert ${i}, research ${j}`);
                    }
                } else {
                    // Если значение пустое, очищаем поле
                    const input = matrixContainer.querySelector(`#experts_data_table_${j}_${i}`);
                    if (input) {
                        input.value = '';
                        console.log(`Cleared experts data value for expert ${i}, research ${j}`);
                    }
                }
            }
        }
    }

    /**
     * Восстанавливает данные матрицы критериев на странице матрицы альтернатив
     */
    restoreCriteriaMatrixOnAlternativesPage(matrixData) {
        const matrixContainer = document.querySelector('[data-matrix="criteria"]');
        if (!matrixContainer) {
            console.warn('Criteria matrix container not found for restoration on alternatives page.');
            return;
        }

        const size = matrixData.length;
        if (size === 0) {
            console.warn('Matrix data for criteria is empty.');
            return;
        }

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
                        input.value = matrixData[i][j] || '';
                        console.log(`Set criteria value for ${i}_${j} on alternatives page: ${matrixData[i][j]}`);
                    } else {
                        console.warn(`Criteria input not found for ${i}_${j} on alternatives page.`);
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
            if (key === 'name_alternatives' || key === 'name_criteria' || key === 'name_conditions' || key === 'names' || key === 'name_research' || key === 'cost_matrix') {
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
        const savageTaskValue = this.getFieldValue('savage_task');
        console.log('Savage task value:', savageTaskValue);

        const formData = {
            task: this.getFieldValue('task') || this.getFieldValue('hierarchy_task') || this.getFieldValue('binary_task') || this.getFieldValue('experts_task') || this.getFieldValue('laplasa_task') || this.getFieldValue('maximin_task') || this.getFieldValue('hurwitz_task') || savageTaskValue,
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
        console.log('- name_criteria:', document.querySelectorAll('input[name="name_criteria"]').length);
        console.log('- name_research:', document.querySelectorAll('input[name="name_research"]').length);
        console.log('- num_alternatives:', document.querySelectorAll('input[name="num_alternatives"]').length);
        console.log('- num_criteria:', document.querySelectorAll('input[name="num_criteria"]').length);
        console.log('- num_experts:', document.querySelectorAll('input[name="num_experts"]').length);
        console.log('- matrix_competence:', document.querySelectorAll('input[name="matrix_competence"]').length);
        console.log('- hierarchy_task:', document.querySelector('textarea[name="hierarchy_task"]') ? 'found' : 'not found');
        console.log('- matrix_krit:', document.querySelectorAll('input[name="matrix_krit"]').length);

        // Отладочная информация для research и competence
        console.log('Research names:', formData.research);
        console.log('Competence matrix:', formData.matrices.competence);

        return formData;
    }

    /**
     * Получает значение поля формы
     */
    getFieldValue(fieldName) {
        // Сначала ищем обычные поля
        let element = document.querySelector(`[name="${fieldName}"]`);

        // Если не найдено, ищем скрытые поля
        if (!element) {
            element = document.querySelector(`input[name="${fieldName}"][type="hidden"]`);
        }

        if (fieldName === 'savage_task') {
            console.log(`Looking for savage_task field:`, element);
            if (element) {
                console.log(`savage_task value:`, element.value);
            }
        }

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
        // Сначала пробуем получить имена из скрытых полей
        const hiddenInputs = document.querySelectorAll('input[name="names"][type="hidden"]');
        if (hiddenInputs.length > 0) {
            const names = [];
            hiddenInputs.forEach((input, index) => {
                names[index] = input.value || '';
            });
            console.log('Objects names from hidden fields:', names);
            return names;
        }

        // Если скрытых полей нет, пробуем получить из обычных полей
        const inputs = document.querySelectorAll('input[name="names"]:not([type="hidden"])');
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

        console.log('Objects names from regular fields:', names);
        return names;
    }

    /**
     * Собирает имена исследований (для Experts)
     */
    getResearchNames() {
        const inputs = document.querySelectorAll('input[name="name_research"]');
        const names = new Array(inputs.length);

        inputs.forEach((input, index) => {
            // Сначала пробуем получить индекс из data-index
            const dataIndex = input.getAttribute('data-index');
            if (dataIndex !== null) {
                const idx = parseInt(dataIndex);
                if (!isNaN(idx) && idx >= 0 && idx < names.length) {
                    names[idx] = input.value || '';
                }
            } else {
                // Если data-index нет, используем порядковый номер в коллекции
                if (index >= 0 && index < names.length) {
                    names[index] = input.value || '';
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
        console.log('Gathering matrices...');

        // Собираем матрицу критериев
        const criteriaMatrix = this.gatherMatrix('criteria');
        console.log('Criteria matrix gathered:', criteriaMatrix);
        if (criteriaMatrix) {
            matrices.criteria = criteriaMatrix;
        }

        // Если матрица критериев не найдена через data-matrix, пробуем собрать из скрытых полей
        if (!criteriaMatrix) {
            console.log('Trying to gather criteria matrix from hidden fields...');
            const hiddenCriteriaMatrix = this.gatherHiddenCriteriaMatrix();
            if (hiddenCriteriaMatrix) {
                matrices.criteria = hiddenCriteriaMatrix;
                console.log('Hidden criteria matrix gathered:', hiddenCriteriaMatrix);
            }
        }

        // Собираем матрицы альтернатив
        const alternativesMatrices = this.gatherAlternativesMatrices();
        console.log('Alternatives matrices gathered:', alternativesMatrices);
        if (Object.keys(alternativesMatrices).length > 0) {
            matrices.alternatives = alternativesMatrices;
        }

        // Собираем матрицу бинарных отношений
        const binaryMatrix = this.gatherBinaryMatrix();
        console.log('Binary matrix gathered:', binaryMatrix);
        if (binaryMatrix) {
            matrices.binary = binaryMatrix;
        }

        // Собираем матрицу компетенции экспертов
        const competenceMatrix = this.gatherCompetenceMatrix();
        console.log('Competence matrix gathered:', competenceMatrix);
        if (competenceMatrix) {
            matrices.competence = competenceMatrix;
        }

        // Собираем матрицу экспертных данных
        const expertsDataMatrix = this.gatherExpertsDataMatrix();
        console.log('Experts data matrix gathered:', expertsDataMatrix);
        if (expertsDataMatrix) {
            matrices.expertsData = expertsDataMatrix;
        }

        // Собираем матрицу Лапласа (только если есть соответствующий контейнер)
        const laplasaContainer = document.querySelector('[data-matrix="laplasa"]');
        if (laplasaContainer) {
            const laplasaMatrix = this.gatherLaplasaMatrix();
            console.log('Laplasa matrix gathered:', laplasaMatrix);
            if (laplasaMatrix) {
                matrices.cost = laplasaMatrix;
            }
        }

        // Собираем матрицу максимина (только если есть соответствующий контейнер)
        const maximinContainer = document.querySelector('[data-matrix="maximin"]');
        if (maximinContainer) {
            const maximinMatrix = this.gatherMaximinMatrix();
            console.log('Maximin matrix gathered:', maximinMatrix);
            if (maximinMatrix) {
                matrices.maximin = maximinMatrix;
            }
        }

        // Собираем матрицу Севіджа (только если есть соответствующий контейнер)
        const savageContainer = document.querySelector('[data-matrix="savage"]');
        if (savageContainer) {
            const savageMatrix = this.gatherSavageMatrix();
            console.log('Savage matrix gathered:', savageMatrix);
            if (savageMatrix) {
                matrices.savage = savageMatrix;
            }
        }

        // Собираем матрицу Гурвица (только если есть соответствующий контейнер)
        const hurwitzContainer = document.querySelector('[data-matrix="hurwitz"]');
        if (hurwitzContainer) {
            const hurwitzMatrix = this.gatherHurwitzMatrix();
            console.log('Hurwitz matrix gathered:', hurwitzMatrix);
            if (hurwitzMatrix) {
                matrices.hurwitz = hurwitzMatrix;
            }
        }

        console.log('Final matrices object:', matrices);
        return matrices;
    }

    /**
    * Собирает конкретную матрицу
    */
    gatherMatrix(matrixType) {
        console.log(`Gathering matrix: ${matrixType}`);
        const matrixContainer = document.querySelector(`[data-matrix="${matrixType}"]`);
        if (!matrixContainer) {
            console.log(`Matrix container not found for: ${matrixType}`);
            return null;
        }

        let inputs = null;
        let size = 0;

        if (matrixType === 'criteria') {
            // Для матрицы критериев используем все поля с name="matrix_krit"
            inputs = matrixContainer.querySelectorAll('input[name="matrix_krit"]');
            console.log(`Found ${inputs.length} matrix_krit inputs`);
            if (inputs.length === 0) return null;

            // Определяем размер матрицы по количеству строк в таблице
            const rows = matrixContainer.querySelectorAll('tbody tr');
            size = rows.length;
            console.log(`Matrix size determined from rows: ${size}`);
            if (size === 0) return null;

            // Создаем матрицу и заполняем её данными
            const matrix = [];
            for (let i = 0; i < size; i++) {
                matrix[i] = [];
                for (let j = 0; j < size; j++) {
                    if (i === j) {
                        // Диагональные элементы всегда 1
                        matrix[i][j] = '1';
                    } else {
                        // Ищем соответствующий input
                        let input = null;
                        if (i < j) {
                            // Верхняя часть матрицы
                            input = matrixContainer.querySelector(`#matrix_krit_up_${i}_${j}`);
                        } else {
                            // Нижняя часть матрицы
                            input = matrixContainer.querySelector(`#matrix_krit_low_${i}_${j}`);
                        }

                        if (input) {
                            matrix[i][j] = input.value || '';
                        } else {
                            matrix[i][j] = '';
                        }
                    }
                }
            }

            console.log(`Criteria matrix built:`, matrix);
            return matrix;
        } else {
            // Для других матриц используем текстовые поля
            inputs = matrixContainer.querySelectorAll('input[type="text"]');
            if (inputs.length === 0) return null;
            // Определяем размер матрицы по количеству строк
            const rows = matrixContainer.querySelectorAll('tbody tr');
            size = rows.length;
            if (size === 0) return null;
        }

        const matrix = [];
        for (let i = 0; i < size; i++) {
            matrix[i] = [];
            for (let j = 0; j < size; j++) {
                // Ищем соответствующий input по имени поля
                let input = null;

                if (matrixType.startsWith('alternatives_')) {
                    // Для матриц альтернатив используем новые имена полей
                    const criteriaNum = matrixType.replace('alternatives_', '');
                    input = matrixContainer.querySelector(`[name="matrix_alt_${criteriaNum}_${i}_${j}"]`);
                } else if (matrixType === 'criteria') {
                    // Для матрицы критериев используем старые имена (fallback)
                    if (i < j) {
                        input = matrixContainer.querySelector(`#matrix_krit_up_${i}_${j}`);
                    } else if (i > j) {
                        input = matrixContainer.querySelector(`#matrix_krit_low_${i}_${j}`);
                    } else {
                        input = matrixContainer.querySelector(`#matrix_krit_diag_${i}_${j}`);
                    }
                } else {
                    // Для других матриц используем старые имена (fallback)
                    if (i < j) {
                        input = matrixContainer.querySelector(`#matrix_krit_up_${i}_${j}`);
                    } else if (i > j) {
                        input = matrixContainer.querySelector(`#matrix_krit_low_${i}_${j}`);
                    } else {
                        input = matrixContainer.querySelector(`#matrix_krit_diag_${i}_${j}`);
                    }
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
    * Собирает данные матрицы критериев из скрытых полей
    */
    gatherHiddenCriteriaMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="criteria"]');
        if (!matrixContainer) {
            console.log('Criteria matrix container not found for hidden gathering.');
            return null;
        }

        const inputs = matrixContainer.querySelectorAll('input[name="matrix_krit"]');
        if (inputs.length === 0) {
            console.log('No hidden matrix_krit inputs found.');
            return null;
        }

        const size = Math.sqrt(inputs.length);
        if (size * size !== inputs.length) {
            console.warn('Number of hidden matrix_krit inputs does not form a square matrix.');
            return null;
        }

        const matrix = [];
        for (let i = 0; i < size; i++) {
            matrix[i] = [];
            for (let j = 0; j < size; j++) {
                const inputIndex = i * size + j;
                if (inputs[inputIndex]) {
                    matrix[i][j] = inputs[inputIndex].value || '';
                } else {
                    matrix[i][j] = '';
                }
            }
        }
        console.log('Hidden criteria matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Собирает данные матрицы бинарных отношений
    */
    gatherBinaryMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="binary"]');
        if (!matrixContainer) {
            console.log('Binary matrix container not found for gathering.');
            return null;
        }

        const inputs = matrixContainer.querySelectorAll('input[name="matrix_binary"]');
        if (inputs.length === 0) {
            console.log('No binary relation inputs found.');
            return null;
        }

        const size = Math.sqrt(inputs.length);
        if (size * size !== inputs.length) {
            console.warn('Number of binary relation inputs does not form a square matrix.');
            return null;
        }

        const matrix = [];
        for (let i = 0; i < size; i++) {
            matrix[i] = [];
            for (let j = 0; j < size; j++) {
                const inputIndex = i * size + j;
                if (inputs[inputIndex]) {
                    matrix[i][j] = inputs[inputIndex].value || '';
                } else {
                    matrix[i][j] = '';
                }
            }
        }
        console.log('Binary relation matrix gathered:', matrix);
        return matrix;
    }

    /**
     * Собирает данные матрицы компетенции экспертов
     */
    gatherCompetenceMatrix() {
        // Сначала пробуем найти контейнер с data-matrix="competence"
        let matrixContainer = document.querySelector('[data-matrix="competence"]');

        if (!matrixContainer) {
            console.log('Competence matrix container not found, trying to gather from hidden fields...');

            // Если контейнер не найден, пробуем собрать из скрытых полей matrix_competence
            const hiddenInputs = document.querySelectorAll('input[name="matrix_competence"]');
            if (hiddenInputs.length > 0) {
                console.log(`Found ${hiddenInputs.length} hidden matrix_competence inputs`);

                // Определяем размер матрицы по количеству экспертов и аргументов
                const numExperts = parseInt(document.querySelector('input[name="num_experts"]')?.value || '2');
                const numArguments = 5; // Стандартное количество аргументов компетенции

                console.log(`Matrix size from hidden fields: ${numExperts} experts x ${numArguments} arguments`);

                // Создаем матрицу и заполняем её данными из скрытых полей
                const matrix = [];
                for (let i = 0; i < numExperts; i++) {
                    matrix[i] = [];
                    for (let j = 0; j < numArguments; j++) {
                        const inputIndex = i * numArguments + j;
                        if (hiddenInputs[inputIndex]) {
                            matrix[i][j] = hiddenInputs[inputIndex].value || '0.0';
                        } else {
                            matrix[i][j] = '0.0';
                        }
                    }
                }

                console.log('Competence matrix gathered from hidden fields:', matrix);
                return matrix;
            }

            console.log('No competence matrix inputs found.');
            return null;
        }

        // Ищем все поля с именем matrix_competence
        const inputs = matrixContainer.querySelectorAll('input[name="matrix_competence"]');
        console.log(`Found ${inputs.length} matrix_competence inputs`);

        if (inputs.length === 0) {
            console.log('No competence matrix inputs found.');
            return null;
        }

        // Определяем размер матрицы по количеству строк и столбцов
        const rows = matrixContainer.querySelectorAll('tbody tr');
        const numExperts = rows.length;
        const numArguments = matrixContainer.querySelectorAll('thead th').length - 1; // -1 для пустой ячейки

        console.log(`Matrix size: ${numExperts} experts x ${numArguments} arguments`);

        if (numExperts === 0 || numArguments === 0) {
            console.warn('Cannot determine matrix size from DOM');
            return null;
        }

        // Создаем матрицу и заполняем её данными
        const matrix = [];
        for (let i = 0; i < numExperts; i++) {
            matrix[i] = [];
            for (let j = 0; j < numArguments; j++) {
                // Ищем соответствующий input по ID
                const input = matrixContainer.querySelector(`#table_competence_${j}_${i}`);
                if (input) {
                    matrix[i][j] = input.value || '';
                } else {
                    matrix[i][j] = '';
                }
            }
        }

        console.log('Competence matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Собирает данные матрицы экспертных данных
    */
    gatherExpertsDataMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="experts_data"]');
        if (!matrixContainer) {
            console.log('Experts data matrix container not found for gathering.');
            return null;
        }

        // Ищем все поля с именем matrix_experts_data
        const inputs = matrixContainer.querySelectorAll('input[name="matrix_experts_data"]');
        console.log(`Found ${inputs.length} matrix_experts_data inputs`);

        if (inputs.length === 0) {
            console.log('No experts data matrix inputs found.');
            return null;
        }

        // Определяем размер матрицы по количеству строк и столбцов
        const rows = matrixContainer.querySelectorAll('tbody tr');
        const numExperts = rows.length;
        const numResearch = matrixContainer.querySelectorAll('thead th').length - 1; // -1 для ячейки "Експерти"

        console.log(`Matrix size: ${numExperts} experts x ${numResearch} research areas`);

        if (numExperts === 0 || numResearch === 0) {
            console.warn('Cannot determine matrix size from DOM');
            return null;
        }

        // Создаем матрицу и заполняем её данными
        const matrix = [];
        for (let i = 0; i < numExperts; i++) {
            matrix[i] = [];
            for (let j = 0; j < numResearch; j++) {
                // Ищем соответствующий input по ID
                const input = matrixContainer.querySelector(`#experts_data_table_${j}_${i}`);
                if (input) {
                    const value = input.value || '';
                    matrix[i][j] = value;
                    console.log(`Expert ${i}, Research ${j}: ID=#experts_data_table_${j}_${i}, Value="${value}"`);
                } else {
                    matrix[i][j] = '';
                    console.warn(`Input not found for Expert ${i}, Research ${j}: ID=#experts_data_table_${j}_${i}`);
                }
            }
        }

        console.log('Experts data matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Собирает другие данные форм
    */
    gatherOtherData() {
        const otherData = {};
        const otherInputs = document.querySelectorAll('input:not([name="task"]):not([name="num_alternatives"]):not([name="num_criteria"]):not([name="name_alternatives"]):not([name="name_criteria"]):not([name="matrix_krit"]):not([name^="matrix_alt_"]):not([name="cost_matrix"]), textarea:not([name="task"]), select');

        otherInputs.forEach(input => {
            if (input.name && input.name !== 'name_alternatives' && input.name !== 'name_criteria' && input.name !== 'matrix_krit' && !input.name.startsWith('matrix_alt_') && input.name !== 'matrix_binary' && input.name !== 'matrix_competence' && input.name !== 'matrix_experts_data' && input.name !== 'cost_matrix') {
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
     * Проверяет, авторизован ли пользователь
     */
    isUserAuthenticated() {
        // Проверяем наличие элементов, которые показывают авторизованного пользователя
        const userElements = document.querySelectorAll('[data-user], .user-info, .profile-link');
        return userElements.length > 0;
    }

    /**
     * Сохраняет черновик
     */
    async saveDraft(title = null, isAutoSave = false) {
        try {
            console.log('💾 saveDraft called with:', { title, isAutoSave, isAutoSaving: this.isAutoSaving });

            // Проверяем, что пользователь авторизован
            if (!this.isUserAuthenticated()) {
                this.showNotification('Потрібно увійти в систему для збереження чернетки', 'error');
                return;
            }

            // Предотвращаем одновременные сохранения только для ручных сохранений
            if (this.isAutoSaving && !isAutoSave) {
                console.log('❌ Auto-save in progress, skipping manual save');
                return;
            }

            const formData = this.gatherFormData();

            // Проверяем, есть ли изменения
            if (this.lastSavedData && JSON.stringify(formData) === JSON.stringify(this.lastSavedData)) {
                this.showNotification('Немає змін для збереження', 'info');
                return;
            }

            // Если это автосохранение и не указан заголовок, создаем автоматический
            let draftTitle = title;
            if (isAutoSave && !title) {
                const methodType = this.getCurrentMethodType();
                const methodNames = {
                    'hierarchy': 'Ієрархічний аналіз',
                    'binary': 'Бінарні відношення',
                    'experts': 'Експертна оцінка',
                    'laplasa': 'Критерій Лапласа',
                    'maximin': 'Критерій Вальда',
                    'savage': 'Критерій Севіджа',
                    'hurwitz': 'Критерій Гурвіца'
                };
                const methodName = methodNames[methodType] || methodType;
                const now = new Date();
                const timeString = now.toLocaleTimeString('uk-UA', {
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: 'Europe/Kiev'
                });
                draftTitle = `${methodName} (автозбереження ${timeString})`;
            }

            const draftData = {
                method_type: this.getCurrentMethodType(),
                current_route: window.location.pathname,
                form_data: formData,
                title: draftTitle,
                is_auto_save: isAutoSave
            };
            console.log('📤 Sending draft data:', draftData);




            const response = await fetch('/drafts/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(draftData)
            });

            console.log('📥 Server response status:', response.status);
            const responseData = await response.json();
            console.log('📥 Server response data:', responseData);

            if (!response.ok) {
                console.error('Server error response:', responseData);
                throw new Error(`Failed to save draft: ${response.status} ${response.statusText}`);
            }

            // Проверяем, что ответ является JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Non-JSON response:', responseData);
                throw new Error('Server returned non-JSON response');
            }

            const result = responseData;
            this.currentDraftId = result.draft_id;
            this.lastSavedData = formData;

            // Показываем разное уведомление для автосохранения
            if (isAutoSave) {
                this.showNotification('🔄 Чернетку автоматично збережено', 'info');
            } else {
                this.showNotification('Чернетку збережено', 'success');
            }

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
        if (path === '/binary' || path.startsWith('/binary/') || path === '/binary_relations' || path.startsWith('/binary_relations/')) return 'binary';
        if (path === '/experts' || path.startsWith('/experts/')) return 'experts';
        if (path === '/laplasa' || path.startsWith('/laplasa/') || path === '/kriteriy_laplasa' || path.startsWith('/kriteriy_laplasa/')) return 'laplasa';
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
        console.log('🔄 Starting auto-save interval...');
        // Автосохранение каждые 2 минуты только на страницах методов
        this.autoSaveInterval = setInterval(() => {
            console.log('🔄 Auto-save check triggered, isAutoSaving:', this.isAutoSaving);
            // Дополнительная проверка: не сохраняем на страницах с результатами
            if (!this.isResultPage() && this.hasFormData() && !this.isAutoSaving) {
                console.log('🔄 Starting auto-save...');
                this.isAutoSaving = true;
                this.saveDraft(null, true).finally(() => {
                    console.log('🔄 Auto-save completed');
                    this.isAutoSaving = false;
                }); // true = isAutoSave
            } else {
                console.log('🔄 Auto-save skipped - conditions not met');
            }
        }, 120000); // 2 минуты
    }

    /**
 * Проверяет, есть ли данные для сохранения
 */
    hasFormData() {
        const formData = this.gatherFormData();
        console.log('📊 Checking form data for auto-save:', formData);

        const hasData = formData.task ||
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
            (formData.matrices && Object.keys(formData.matrices).length > 0) ||
            (formData.matrixType && formData.matrixType.trim() !== '');

        console.log('📊 Has form data result:', hasData);
        return hasData;
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
                    console.log('Internal navigation detected: link click');
                } else if (target.tagName === 'BUTTON' || target.type === 'submit') {
                    // Это кнопка, которая может вести к навигации
                    const form = target.closest('form');
                    if (form) {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                        console.log('Internal navigation detected: form button');
                    }

                    // Проверяем текст кнопки на наличие слов навигации
                    const buttonText = target.textContent.toLowerCase();
                    if (buttonText.includes('далі') || buttonText.includes('дальше') ||
                        buttonText.includes('next') || buttonText.includes('продовжити') ||
                        buttonText.includes('continue') || buttonText.includes('вперед') ||
                        buttonText.includes('submit') || buttonText.includes('відправити') ||
                        buttonText.includes('завершити') || buttonText.includes('finish')) {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                        console.log('Internal navigation detected: navigation button');
                    }

                    // Проверяем атрибуты кнопки
                    const buttonType = target.getAttribute('type');
                    if (buttonType === 'submit') {
                        sessionStorage.setItem('isInternalNavigation', 'true');
                        console.log('Internal navigation detected: submit button');
                    }
                }
            }
        });

        // Перехватываем отправку форм
        document.addEventListener('submit', (event) => {
            // Все формы считаем внутренней навигацией
            sessionStorage.setItem('isInternalNavigation', 'true');
            console.log('Internal navigation detected: form submit');
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
            console.log('BeforeUnload: Internal navigation detected, no warning shown');
            return;
        }

        // Дополнительная проверка: если это переход на другую страницу того же сайта, не показываем предупреждение
        if (event.target && event.target.location) {
            const currentHost = window.location.hostname;
            const targetHost = event.target.location.hostname;

            if (currentHost === targetHost) {
                console.log('BeforeUnload: Same host navigation, no warning shown');
                return;
            }
        }

        // Проверяем, есть ли несохраненные изменения
        if (this.hasUnsavedChanges()) {
            // Показываем предупреждение только если есть реальные изменения
            console.log('BeforeUnload: Unsaved changes detected, showing warning');
            event.preventDefault();
            event.returnValue = 'У вас є незбережені зміни. Дійсно хочете покинути сторінку?';
            return event.returnValue;
        }

        // Если нет изменений, не показываем предупреждение
        console.log('BeforeUnload: No changes detected, no warning shown');
        return;
    }

    /**
 * Проверяет, есть ли несохраненные изменения
 */
    hasUnsavedChanges() {
        // Если нет сохраненных данных, не показываем предупреждение
        if (!this.lastSavedData) {
            console.log('hasUnsavedChanges: No lastSavedData, no warning shown');
            return false;
        }

        const currentData = this.gatherFormData();
        const hasChanges = JSON.stringify(currentData) !== JSON.stringify(this.lastSavedData);

        console.log('hasUnsavedChanges: Current data:', currentData);
        console.log('hasUnsavedChanges: Last saved data:', this.lastSavedData);
        console.log('hasUnsavedChanges: Has changes:', hasChanges);

        return hasChanges;
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
     * Проверяет, является ли текущая страница страницей с результатами
     * Учитывает различные варианты названий страниц с результатами
     * @returns {boolean} true если это страница с результатами, false в противном случае
     */
    isResultPage() {
        const currentPath = window.location.pathname;
        console.log('isResultPage check for path:', currentPath);

        const isResult = currentPath.includes('/result') ||
            currentPath.includes('/experts_result') ||
            currentPath.endsWith('/result') ||
            currentPath.endsWith('/experts_result') ||
            currentPath.includes('/result/') ||
            currentPath.includes('/experts_result/');

        console.log('isResultPage result:', isResult);
        return isResult;
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
        const currentPath = window.location.pathname;

        // Проверяем, является ли это страницей с результатом
        const isResultPage = this.isResultPage();

        console.log('Current path:', currentPath);
        console.log('Method type:', methodType);
        console.log('Is method page:', isMethodPage);
        console.log('Is result page:', isResultPage);
        console.log('Save button element:', saveButton);
        console.log('Save button current display:', saveButton.style.display);

        // Показываем кнопку только на страницах методов, но НЕ на страницах с результатами
        // Это предотвращает сохранение черновиков на страницах, где уже показаны результаты
        if (isMethodPage && !isResultPage) {
            saveButton.style.display = 'block';
            console.log('Save button shown - method page without results');
            console.log('Method details:', { methodType, isMethodPage, isResultPage, currentPath });
        } else {
            saveButton.style.display = 'none';
            console.log('Save button hidden - either not a method page or result page');
            console.log('Hidden details:', { methodType, isMethodPage, isResultPage, currentPath });
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
     * Помечает все ссылки на странице как внутренние
     */
    markAllPageLinks() {
        // Помечаем все существующие ссылки
        const allLinks = document.querySelectorAll('a[href]');
        allLinks.forEach(link => {
            if (link.href && !link.href.startsWith('javascript:') && !link.href.startsWith('#')) {
                link.addEventListener('click', () => {
                    sessionStorage.setItem('isInternalNavigation', 'true');
                    console.log('DraftsManager: Link marked as internal navigation:', link.href);
                });
            }
        });

        // Помечаем все кнопки
        const allButtons = document.querySelectorAll('button, input[type="submit"]');
        allButtons.forEach(button => {
            button.addEventListener('click', () => {
                sessionStorage.setItem('isInternalNavigation', 'true');
                console.log('DraftsManager: Button marked as internal navigation');
            });
        });

        // Помечаем все формы
        const allForms = document.querySelectorAll('form');
        allForms.forEach(form => {
            form.addEventListener('submit', () => {
                sessionStorage.setItem('isInternalNavigation', 'true');
                console.log('DraftsManager: Form marked as internal navigation');
            });
        });
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

    /**
    * Собирает данные матрицы максимина
    */
    gatherMaximinMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="maximin"]');
        if (!matrixContainer) {
            console.log('Maximin matrix container not found');
            return null;
        }

        // Ищем все поля с именем cost_matrix
        const inputs = matrixContainer.querySelectorAll('input[name="cost_matrix"]');
        console.log(`Found ${inputs.length} cost_matrix inputs`);

        if (inputs.length === 0) {
            console.log('No cost matrix inputs found.');
            return null;
        }

        // Определяем размер матрицы по количеству строк и столбцов
        const rows = matrixContainer.querySelectorAll('tbody tr');
        const numAlt = rows.length;
        const numConditions = matrixContainer.querySelectorAll('thead th').length - 1; // -1 для пустой ячейки

        console.log(`Matrix size: ${numAlt} alternatives x ${numConditions} conditions`);

        if (numAlt === 0 || numConditions === 0) {
            console.warn('Cannot determine matrix size from DOM');
            return null;
        }

        // Создаем матрицу и заполняем её данными
        const matrix = [];
        for (let i = 0; i < numAlt; i++) {
            matrix[i] = [];
            for (let j = 0; j < numConditions; j++) {
                // Ищем соответствующий input по ID
                const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                if (input) {
                    const value = input.value.trim();
                    // Сохраняем пустую строку для пустых полей, а не '0'
                    matrix[i][j] = value === '' ? '' : value;
                } else {
                    matrix[i][j] = '';
                }
            }
        }

        console.log('Maximin matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Собирает данные матрицы Севіджа
    */
    gatherSavageMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="savage"]');
        if (!matrixContainer) {
            console.log('Savage matrix container not found');
            return null;
        }

        // Ищем все поля с именем cost_matrix
        const inputs = matrixContainer.querySelectorAll('input[name="cost_matrix"]');
        console.log(`Found ${inputs.length} cost_matrix inputs`);

        if (inputs.length === 0) {
            console.log('No Savage matrix inputs found.');
            return null;
        }

        // Определяем размер матрицы по количеству альтернатив и условий
        const numAlt = parseInt(document.querySelector('input[name="num_alt"]')?.value || '2');
        const numConditions = parseInt(document.querySelector('input[name="num_conditions"]')?.value || '2');

        console.log(`Savage matrix size: ${numAlt} alternatives x ${numConditions} conditions`);

        // Создаем матрицу и заполняем её данными
        const matrix = [];
        for (let i = 0; i < numAlt; i++) {
            matrix[i] = [];
            for (let j = 0; j < numConditions; j++) {
                // Ищем соответствующий input по ID
                const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                if (input) {
                    const value = input.value.trim();
                    // Сохраняем пустую строку для пустых полей, а не '0'
                    matrix[i][j] = value === '' ? '' : value;
                } else {
                    matrix[i][j] = '';
                }
            }
        }

        console.log('Savage matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Собирает данные матрицы Гурвица
    */
    gatherHurwitzMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="hurwitz"]');
        if (!matrixContainer) {
            console.log('Hurwitz matrix container not found');
            return null;
        }

        // Ищем все поля с именем cost_matrix
        const inputs = matrixContainer.querySelectorAll('input[name="cost_matrix"]');
        console.log(`Found ${inputs.length} cost_matrix inputs`);

        if (inputs.length === 0) {
            console.log('No Hurwitz matrix inputs found.');
            return null;
        }

        // Определяем размер матрицы по количеству альтернатив и условий
        const numAlt = parseInt(document.querySelector('input[name="num_alt"]')?.value || '2');
        const numConditions = parseInt(document.querySelector('input[name="num_conditions"]')?.value || '2');

        console.log(`Hurwitz matrix size: ${numAlt} alternatives x ${numConditions} conditions`);

        // Создаем матрицу и заполняем её данными
        const matrix = [];
        for (let i = 0; i < numAlt; i++) {
            matrix[i] = [];
            for (let j = 0; j < numConditions; j++) {
                // Ищем соответствующий input по ID
                const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                if (input) {
                    const value = input.value.trim();
                    // Сохраняем пустую строку для пустых полей, а не '0'
                    matrix[i][j] = value === '' ? '' : value;
                } else {
                    matrix[i][j] = '';
                }
            }
        }

        console.log('Hurwitz matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Собирает данные матрицы Лапласа
    */
    gatherLaplasaMatrix() {
        const matrixContainer = document.querySelector('[data-matrix="laplasa"]');
        if (!matrixContainer) {
            console.log('Laplasa matrix container not found');
            return null;
        }

        // Ищем все поля с именем cost_matrix
        const inputs = matrixContainer.querySelectorAll('input[name="cost_matrix"]');
        console.log(`Found ${inputs.length} cost_matrix inputs`);

        if (inputs.length === 0) {
            console.log('No cost matrix inputs found.');
            return null;
        }

        // Определяем размер матрицы по количеству строк и столбцов
        const rows = matrixContainer.querySelectorAll('tbody tr');
        const numAlt = rows.length;
        const numConditions = matrixContainer.querySelectorAll('thead th').length - 1; // -1 для пустой ячейки

        console.log(`Matrix size: ${numAlt} alternatives x ${numConditions} conditions`);

        if (numAlt === 0 || numConditions === 0) {
            console.warn('Cannot determine matrix size from DOM');
            return null;
        }

        // Создаем матрицу и заполняем её данными
        const matrix = [];
        for (let i = 0; i < numAlt; i++) {
            matrix[i] = [];
            for (let j = 0; j < numConditions; j++) {
                // Ищем соответствующий input по ID
                const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                if (input) {
                    const value = input.value.trim();
                    // Сохраняем пустую строку для пустых полей, а не '0'
                    matrix[i][j] = value === '' ? '' : value;
                } else {
                    matrix[i][j] = '';
                }
            }
        }

        console.log('Laplasa matrix gathered:', matrix);
        return matrix;
    }

    /**
    * Восстанавливает матрицу максимина
    */
    restoreMaximinMatrix(matrixData) {
        console.log('=== RESTORING MAXIMIN MATRIX ===');
        console.log('Input matrixData:', matrixData);
        console.log('Type of matrixData:', typeof matrixData);
        console.log('Is array:', Array.isArray(matrixData));

        const matrixContainer = document.querySelector('[data-matrix="maximin"]');
        if (!matrixContainer) {
            console.warn('Maximin matrix container not found for restoration.');
            return;
        }

        const numAlt = matrixData.length;
        if (numAlt === 0) {
            console.warn('Matrix data for Maximin is empty.');
            return;
        }

        const numConditions = matrixData[0] ? matrixData[0].length : 0;
        console.log('Matrix size:', numAlt, 'x', numConditions);
        console.log('Matrix data:', matrixData);
        console.log('Matrix container found:', !!matrixContainer);

        // Восстанавливаем матрицу по ID полей
        for (let i = 0; i < numAlt; i++) {
            for (let j = 0; j < numConditions; j++) {
                const currentValue = matrixData[i] ? matrixData[i][j] : undefined;
                console.log(`Processing [${i}][${j}]: value="${currentValue}", type=${typeof currentValue}`);

                // Проверяем, есть ли значение в матрице
                if (currentValue !== undefined && currentValue !== '' && currentValue !== null) {
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = currentValue;
                        console.log(`✓ Set Maximin value for alternative ${i}, condition ${j}: "${currentValue}"`);
                    } else {
                        console.warn(`✗ Maximin input not found for alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                } else {
                    // Если значение пустое, очищаем поле
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = '';
                        console.log(`- Cleared Maximin value for alternative ${i}, condition ${j}`);
                    } else {
                        console.warn(`✗ Input not found for clearing alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                }
            }
        }
        console.log('=== MAXIMIN MATRIX RESTORATION COMPLETED ===');
    }

    /**
    * Восстанавливает матрицу Севіджа
    */
    restoreSavageMatrix(matrixData) {
        console.log('=== RESTORING SAVAGE MATRIX ===');
        console.log('Input matrixData:', matrixData);
        console.log('Type of matrixData:', typeof matrixData);
        console.log('Is array:', Array.isArray(matrixData));

        const matrixContainer = document.querySelector('[data-matrix="savage"]');
        if (!matrixContainer) {
            console.warn('Savage matrix container not found for restoration.');
            return;
        }

        if (!matrixData || !Array.isArray(matrixData)) {
            console.warn('Invalid Savage matrix data for restoration.');
            return;
        }

        // Определяем размер матрицы
        const numAlt = parseInt(document.querySelector('input[name="num_alt"]')?.value || '2');
        const numConditions = parseInt(document.querySelector('input[name="num_conditions"]')?.value || '2');

        console.log(`Savage matrix size: ${numAlt} alternatives x ${numConditions} conditions`);

        for (let i = 0; i < numAlt; i++) {
            for (let j = 0; j < numConditions; j++) {
                const currentValue = matrixData[i] ? matrixData[i][j] : undefined;
                console.log(`Processing [${i}][${j}]: value="${currentValue}", type=${typeof currentValue}`);

                // Проверяем, есть ли значение в матрице
                if (currentValue !== undefined && currentValue !== '' && currentValue !== null) {
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = currentValue;
                        console.log(`✓ Set Savage value for alternative ${i}, condition ${j}: "${currentValue}"`);
                    } else {
                        console.warn(`✗ Savage input not found for alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                } else {
                    // Если значение пустое, очищаем поле
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = '';
                        console.log(`- Cleared Savage value for alternative ${i}, condition ${j}`);
                    } else {
                        console.warn(`✗ Input not found for clearing alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                }
            }
        }
        console.log('=== SAVAGE MATRIX RESTORATION COMPLETED ===');
    }

    /**
    * Восстанавливает матрицу Гурвица
    */
    restoreHurwitzMatrix(matrixData) {
        console.log('=== RESTORING HURWITZ MATRIX ===');
        console.log('Input matrixData:', matrixData);
        console.log('Type of matrixData:', typeof matrixData);
        console.log('Is array:', Array.isArray(matrixData));

        const matrixContainer = document.querySelector('[data-matrix="hurwitz"]');
        if (!matrixContainer) {
            console.warn('Hurwitz matrix container not found for restoration.');
            return;
        }

        if (!matrixData || !Array.isArray(matrixData)) {
            console.warn('Invalid Hurwitz matrix data for restoration.');
            return;
        }

        // Определяем размер матрицы
        const numAlt = parseInt(document.querySelector('input[name="num_alt"]')?.value || '2');
        const numConditions = parseInt(document.querySelector('input[name="num_conditions"]')?.value || '2');

        console.log(`Hurwitz matrix size: ${numAlt} alternatives x ${numConditions} conditions`);

        for (let i = 0; i < numAlt; i++) {
            for (let j = 0; j < numConditions; j++) {
                const currentValue = matrixData[i] ? matrixData[i][j] : undefined;
                console.log(`Processing [${i}][${j}]: value="${currentValue}", type=${typeof currentValue}`);

                // Проверяем, есть ли значение в матрице
                if (currentValue !== undefined && currentValue !== '' && currentValue !== null) {
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = currentValue;
                        console.log(`✓ Set Hurwitz value for alternative ${i}, condition ${j}: "${currentValue}"`);
                    } else {
                        console.warn(`✗ Hurwitz input not found for alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                } else {
                    // Если значение пустое, очищаем поле
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = '';
                        console.log(`- Cleared Hurwitz value for alternative ${i}, condition ${j}`);
                    } else {
                        console.warn(`✗ Input not found for clearing alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                }
            }
        }
        console.log('=== HURWITZ MATRIX RESTORATION COMPLETED ===');
    }

    /**
    * Восстанавливает матрицу Лапласа
    */
    restoreLaplasaMatrix(matrixData) {
        console.log('=== RESTORING LAPLASA MATRIX ===');
        console.log('Input matrixData:', matrixData);
        console.log('Type of matrixData:', typeof matrixData);
        console.log('Is array:', Array.isArray(matrixData));

        const matrixContainer = document.querySelector('[data-matrix="laplasa"]');
        if (!matrixContainer) {
            console.warn('Laplasa matrix container not found for restoration.');
            return;
        }

        const numAlt = matrixData.length;
        if (numAlt === 0) {
            console.warn('Matrix data for Laplasa is empty.');
            return;
        }

        const numConditions = matrixData[0] ? matrixData[0].length : 0;
        console.log('Matrix size:', numAlt, 'x', numConditions);
        console.log('Matrix data:', matrixData);
        console.log('Matrix container found:', !!matrixContainer);

        // Восстанавливаем матрицу по ID полей
        for (let i = 0; i < numAlt; i++) {
            for (let j = 0; j < numConditions; j++) {
                const currentValue = matrixData[i] ? matrixData[i][j] : undefined;
                console.log(`Processing [${i}][${j}]: value="${currentValue}", type=${typeof currentValue}`);

                // Проверяем, есть ли значение в матрице
                if (currentValue !== undefined && currentValue !== '' && currentValue !== null) {
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = currentValue;
                        console.log(`✓ Set Laplasa value for alternative ${i}, condition ${j}: "${currentValue}"`);
                    } else {
                        console.warn(`✗ Laplasa input not found for alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                } else {
                    // Если значение пустое, очищаем поле
                    const input = matrixContainer.querySelector(`#cost_matrix_${i}_${j}_`);
                    if (input) {
                        input.value = '';
                        console.log(`- Cleared Laplasa value for alternative ${i}, condition ${j}`);
                    } else {
                        console.warn(`✗ Input not found for clearing alternative ${i}, condition ${j}: ID=#cost_matrix_${i}_${j}_`);
                    }
                }
            }
        }
        console.log('=== LAPLASA MATRIX RESTORATION COMPLETED ===');
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
