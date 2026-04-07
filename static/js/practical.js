window.Editor = (function() {
    let textBlockCounter = 0;
    let hasChanges = false; // Добавляем флаг изменений

    function showNotification(message, type = 'success') {
        const notificationArea = document.getElementById('notification-area');
        const notification = document.createElement('div');

        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.role = 'alert';
        notification.innerHTML = `
            <strong>${type === 'success' ? 'Успех!' : 'Ошибка!'}</strong> ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

        notificationArea.appendChild(notification);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 150);
        }, 5000);
    }

    function addSaveStatus(form) {
        const saveButton = form.querySelector('button[type="submit"]');
        if (!saveButton || form.querySelector('.save-status')) return;

        const statusElement = document.createElement('h6');
        statusElement.className = 'card-description mb-0 d-flex save-status hidden';
        statusElement.innerHTML = 'Несохранено';

        saveButton.parentNode.insertBefore(statusElement, saveButton);
    }

    function showSaveStatus(form, saved = false) {
        const statusElement = form.querySelector('.save-status');
        if (!statusElement) return;

        statusElement.classList.remove('hidden');

        if (saved) {
            statusElement.textContent = 'Сохранено';
            statusElement.classList.add('saved');
            hasChanges = false;

            setTimeout(() => {
                statusElement.classList.add('hidden');
                setTimeout(() => {
                    statusElement.classList.remove('saved');
                    statusElement.textContent = 'Несохранено';
                }, 300);
            }, 3000);
        } else {
            statusElement.textContent = 'Несохранено';
            statusElement.classList.remove('saved');
            hasChanges = true;
        }
    }

    function saveBlock(form) {
        const formData = new FormData(form);
        const blockId = form.querySelector('input[name="id"]').value;
        const blockType = form.querySelector('input[name="type"]').value;

        showSaveStatus(form, true); // Показываем статус сохранения

        fetch(window.djangoContext.editUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': form.querySelector('input[name="csrfmiddlewaretoken"]').value
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Блок успешно сохранен');
                if (blockId === '' && data.id) {
                    form.querySelector('input[name="id"]').value = data.id;
                    form.closest('.card').setAttribute('data-id', data.id);
                }
            } else {
                showNotification(data.error || 'Ошибка при сохранении блока', 'danger');
            }
        })
        .catch(error => {
            showNotification('Ошибка сети: ' + error.message, 'danger');
        });
    }

    function deleteBlock(block) {
        const blockId = block.getAttribute('data-id');
        const blockType = block.getAttribute('data-type');

        if (!blockId) {
            block.remove();
            return;
        }

        if (!confirm('Вы уверены, что хотите удалить этот блок?')) return;

        fetch(window.djangoContext.editUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': window.djangoContext.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'delete',
                id: blockId,
                type: blockType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                block.remove();
                showNotification('Блок успешно удален');
            } else {
                showNotification(data.error || 'Ошибка при удалении блока', 'danger');
            }
        })
        .catch(error => {
            showNotification('Ошибка сети: ' + error.message, 'danger');
        });
    }

    function checkUnsavedChanges() {
        return hasChanges;
    }

    return {
        init: function() {
            document.querySelectorAll('.block-form').forEach(form => {
                addSaveStatus(form);

                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    saveBlock(this);
                });

                // Обработчики изменений для полей
                form.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('input', () => {
                showSaveStatus(form);
            });

            // Для чекбоксов используем событие change
            if (input.type === 'checkbox') {
                input.addEventListener('change', () => {
                    showSaveStatus(form);
                });
            }
        });

                // Обработчик для Trix Editor
                if (form.querySelector('trix-editor')) {
                    form.querySelector('trix-editor').addEventListener('trix-change', () => {
                        showSaveStatus(form);
                    });
                }
            });

            // Обработчик перед закрытием страницы
            window.addEventListener('beforeunload', function(e) {
                if (checkUnsavedChanges()) {
                    e.preventDefault();
                    e.returnValue = 'У вас есть несохраненные изменения. Вы уверены, что хотите покинуть страницу?';
                    return e.returnValue;
                }
            });

            document.addEventListener('click', (e) => {
                if (e.target.closest('.delete-block')) {
                    e.preventDefault();
                    deleteBlock(e.target.closest('.card'));
                }
            });

            document.addEventListener('focusin', function(event) {
                if (event.target.tagName === "TRIX-EDITOR") {
                    const toolbarId = event.target.getAttribute("toolbar");
                    const toolbar = document.getElementById(toolbarId);
                    if (toolbar) toolbar.classList.add("active");
                }
            });

            document.addEventListener('focusout', function(event) {
                if (event.target.tagName === "TRIX-EDITOR") {
                    const toolbarId = event.target.getAttribute("toolbar");
                    const toolbar = document.getElementById(toolbarId);
                    if (toolbar) toolbar.classList.remove("active");
                }
            });
        },

        addTextBlock: function(e) {
            if (e) e.preventDefault();

            textBlockCounter++;
            const container = document.getElementById('blocks-container');
            const editorId = `editor-new-${textBlockCounter}`;
            const toolbarId = `toolbar-${editorId}`;

            const textBlock = `
                <div class="card mb-3" data-id="" data-type="text">
                    <div class="card-body">
                        <form class="block-form" method="post" enctype="multipart/form-data">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${window.djangoContext.csrfToken}">
                            <input type="hidden" name="type" value="text">
                            <input type="hidden" name="id" value="">
                            <div style="margin-left: -15px;" class="form-group d-flex align-items-center justify-content-between">
                                <input name="title" style="border: none; font-size: 20px; font-weight: normal;"
                                    type="text" class="form-control me-3" placeholder="Введите название...">
                                <div class="d-flex gap-3 align-items-center justify-content-center">
                                    <h6 class="card-description mb-0 d-flex save-status hidden">Несохранено</h6>
                                    <button type="submit" style="margin: 5px" class="btn btn-outline-primary">Сохранить</button>
                                    <button type="button" class="btn btn-inverse-danger btn-icon delete-block">
                                        <i class="ti-close"></i>
                                    </button>
                                </div>
                            </div>

                            <trix-toolbar style="margin-top: -25px" id="${toolbarId}"></trix-toolbar>

                            <div style="margin-top: -10px" class="form-group trix-container">
                                <input id="${editorId}" type="hidden" name="body">
                                <trix-editor input="${editorId}" toolbar="${toolbarId}" placeholder="Введите текст..."></trix-editor>
                            </div>
                            <div class="form-check form-check-info">
            <label class="form-check-label">
              <input type="checkbox" class="form-check-input" name="download" >
              Требуется загрузка файла?
            </label>
          </div>
                            <div class="form-group">
                                <input name="step" class="typeahead tt-input" type="number" placeholder="Введите номер шага">
                            </div>
                        </form>
                    </div>
                </div>
            `;

            container.insertAdjacentHTML('beforeend', textBlock);
            container.lastElementChild.scrollIntoView({ behavior: 'smooth' });

            const newForm = container.lastElementChild.querySelector('.block-form');
            newForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveBlock(this);
            });

            // Добавляем обработчики изменений для нового блока
            newForm.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
                input.addEventListener('input', () => {
                    const statusElement = newForm.querySelector('.save-status');
                    if (statusElement) {
                        statusElement.classList.remove('hidden');
                        hasChanges = true;
                    }
                });
            });

            if (newForm.querySelector('trix-editor')) {
                newForm.querySelector('trix-editor').addEventListener('trix-change', () => {
                    const statusElement = newForm.querySelector('.save-status');
                    if (statusElement) {
                        statusElement.classList.remove('hidden');
                        hasChanges = true;
                    }
                });
            }
        },

        addWorkBlock: function(e) {
            if (e) e.preventDefault();

            const container = document.getElementById('blocks-container');

            const workBlock = `
                <div class="card mb-3" data-id="" data-type="work">
                    <div class="card-body">
                        <form class="block-form" method="post" enctype="multipart/form-data">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${window.djangoContext.csrfToken}">
                            <input type="hidden" name="type" value="work">
                            <input type="hidden" name="id" value="">
                            <div style="margin-left: -15px;" class="form-group d-flex align-items-center justify-content-between">
                                <label style="border: none; font-size: 20px; font-weight: normal;" class="form-control me-3">Практическая работа (редактор)</label>
                                <div class="d-flex gap-3 align-items-center justify-content-center">
                                    <h6 class="card-description mb-0 d-flex save-status hidden">Несохранено</h6>
                                    <button type="submit" style="margin: 5px" class="btn btn-outline-primary">Сохранить</button>
                                    <button type="button" class="btn btn-inverse-danger btn-icon delete-block">
                                        <i class="ti-close"></i>
                                    </button>
                                </div>
                            </div>

                            <div class="form-group">
                                <label>Текст задания</label>
                                <textarea name="task" class="form-control" rows="3" placeholder="Введите текст задания..."></textarea>
                            </div>

                            <div class="form-group">
                                <label>Подсказка</label>
                                <textarea name="hint" class="form-control" rows="2" placeholder="Введите подсказку..."></textarea>
                            </div>

                            <div class="form-group">
                                <label>Ожидаемый вывод</label>
                                <textarea name="expected_output" class="form-control" rows="2" placeholder="Введите ожидаемый вывод..."></textarea>
                            </div>

                            <div class="form-group">
                                <input name="step" class="typeahead tt-input" type="number" placeholder="Введите номер шага">
                            </div>
                        </form>
                    </div>
                </div>
            `;

            container.insertAdjacentHTML('beforeend', workBlock);
            container.lastElementChild.scrollIntoView({ behavior: 'smooth' });

            const newForm = container.lastElementChild.querySelector('.block-form');
            newForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveBlock(this);
            });

            // Добавляем обработчики изменений для нового блока
            newForm.querySelectorAll('input, textarea').forEach(input => {
                input.addEventListener('input', () => {
                    const statusElement = newForm.querySelector('.save-status');
                    if (statusElement) {
                        statusElement.classList.remove('hidden');
                        hasChanges = true;
                    }
                });
            });
        }
    };
})();

document.addEventListener('DOMContentLoaded', function() {
    Editor.init();
});
