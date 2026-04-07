// text_test.js

window.Editor = (function () {
  // Приватные переменные
  let textBlockCounter = 0;
  let questions = [];
  let currentTestBlock = null;
  let hasChanges = false;

  // Вспомогательные функции
  function escapeHtml(unsafe) {
    return unsafe
      ? unsafe
          .toString()
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#039;")
      : "";
  }

  function hasUnsavedChanges() {
  // Проверяем все формы на странице
  const forms = document.querySelectorAll('.block-form');
  for (const form of forms) {
    const statusElement = form.querySelector('.save-status');
    if (statusElement && !statusElement.classList.contains('hidden') && !statusElement.classList.contains('saved')) {
      return true;
    }
  }
  return false;
}

function renderQuestions() {
    const container = document.getElementById("questionsContainer");
    container.innerHTML = "";

    questions.forEach((question, qIndex) => {
        const questionElement = document.createElement("div");
        questionElement.className = "card mb-3 question-card";
        questionElement.dataset.index = qIndex;
        questionElement.dataset.type = question.type;

        if (question.type === 'MC') {
            // Вопрос с выбором ответа
            questionElement.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Вопрос ${qIndex + 1} (Выбор ответа)</h6>
                    <button type="button" class="btn btn-sm btn-danger" data-action="remove-question" data-index="${qIndex}">
                        <i class="ti-close"></i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>Текст вопроса</label>
                        <input type="text" class="form-control question-text" value="${escapeHtml(question.text)}"
                            data-index="${qIndex}">
                    </div>
                    <h6 class="mt-3">Варианты ответов</h6>
                    ${question.answers.map((answer, aIndex) => `
                        <div class="input-group mb-2 answer-group" data-qindex="${qIndex}" data-aindex="${aIndex}">
                            <div class="input-group-prepend correct-answer-toggle" style="cursor: pointer;">
                                <span class="input-group-text ${answer.is_correct ? 'bg-success text-white' : 'bg-light'}">
                                    <input type="radio" class="form-check-input correct-answer d-none"
                                        name="correct-answer-${qIndex}" ${answer.is_correct ? "checked" : ""}
                                        data-qindex="${qIndex}" data-aindex="${aIndex}">
                                    ${answer.is_correct ? '✓ Правильный ответ' : 'Отметить правильным'}
                                </span>
                            </div>
                            <input type="text" class="form-control answer-text" value="${escapeHtml(answer.text)}"
                                aria-label="Текст ответа" data-qindex="${qIndex}" data-aindex="${aIndex}">
                            <div class="input-group-append">
                                <button class="btn btn-sm btn-danger" type="button" data-action="remove-answer"
                                    data-qindex="${qIndex}" data-aindex="${aIndex}">
                                    <i class="ti-close"></i>
                                </button>
                            </div>
                        </div>
                    `).join("")}
                    <button type="button" class="btn btn-sm btn-outline-primary mt-2" data-action="add-answer" data-index="${qIndex}">
                        <i class="ti-plus"></i> Добавить ответ
                    </button>
                </div>
            `;
        } else if (question.type === 'FB') {
            // Вопрос на дополнение
            questionElement.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Вопрос ${qIndex + 1} (Дополнение)</h6>
                    <button type="button" class="btn btn-sm btn-danger" data-action="remove-question" data-index="${qIndex}">
                        <i class="ti-close"></i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>Текст вопроса (укажите пропуск как ______)</label>
                        <input type="text" class="form-control question-text" value="${escapeHtml(question.text)}"
                            data-index="${qIndex}" placeholder="Например: Тестирование – форма ______ контроля">
                    </div>
                    <div class="form-group">
                        <label>Правильный ответ</label>
                        <input type="text" class="form-control correct-answer-input"
                            value="${escapeHtml(question.correct_answer || '')}"
                            data-index="${qIndex}" placeholder="Введите правильный ответ для пропуска">
                    </div>
                </div>
            `;
        } else if (question.type === 'MT') {
            // Новый тип - вопрос на соответствие
            questionElement.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">Вопрос ${qIndex + 1} (Соответствие)</h6>
                    <button type="button" class="btn btn-sm btn-danger" data-action="remove-question" data-index="${qIndex}">
                        <i class="ti-close"></i>
                    </button>
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>Текст вопроса</label>
                        <input type="text" class="form-control question-text" value="${escapeHtml(question.text)}"
                            data-index="${qIndex}" placeholder="Например: Сопоставьте термины с определениями">
                    </div>
                    <h6 class="mt-3">Пары соответствия</h6>
                    <div class="matching-pairs-container" data-index="${qIndex}">
                        ${question.pairs ? question.pairs.map((pair, pIndex) => `
                            <div class="form-row mb-2 matching-pair" data-pindex="${pIndex}">
                                <div class="col">
                                    <input type="text" class="form-control term-input"
                                        value="${escapeHtml(pair.term)}"
                                        placeholder="Термин"
                                        data-qindex="${qIndex}"
                                        data-pindex="${pIndex}">
                                </div>
                                <div class="col">
                                    <input type="text" class="form-control definition-input"
                                        value="${escapeHtml(pair.definition)}"
                                        placeholder="Определение"
                                        data-qindex="${qIndex}"
                                        data-pindex="${pIndex}">
                                </div>
                                <div class="col-auto">
                                    <button class="btn btn-sm btn-danger" type="button"
                                        data-action="remove-pair"
                                        data-qindex="${qIndex}"
                                        data-pindex="${pIndex}">
                                        <i class="ti-close"></i>
                                    </button>
                                </div>
                            </div>
                        `).join("") : ''}
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-primary mt-2"
                        data-action="add-pair"
                        data-index="${qIndex}">
                        <i class="ti-plus"></i> Добавить пару
                    </button>
                </div>
            `;
        }

        container.appendChild(questionElement);
    });
}

  function showSuccessMessage(message) {
    const notificationArea = document.getElementById("notification-area");
    const notification = document.createElement("div");

    notification.className = "alert alert-success alert-dismissible fade show";
    notification.role = "alert";
    notification.innerHTML = `
            <strong>Успешно!</strong> ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

    notificationArea.appendChild(notification);

    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 150);
    }, 5000);
  }

  function showErrorMessage(message) {
    const notificationArea = document.getElementById("notification-area");
    const notification = document.createElement("div");

    notification.className = "alert alert-danger alert-dismissible fade show";
    notification.role = "alert";
    notification.innerHTML = `
            <strong>Ошибка!</strong> ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

    notificationArea.appendChild(notification);

    setTimeout(() => {
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 150);
    }, 7000);
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
  // Основные функции
  function loadTestQuestions(testId) {
    fetch(`/api/tests/${testId}/questions/`)
      .then((response) => response.json())
      .then((data) => {
        questions = data.questions || [];
        renderQuestions();
      })
      .catch((error) => {
        console.error("Ошибка загрузки вопросов:", error);
        showErrorMessage("Не удалось загрузить вопросы теста");
      });
  }


  function saveBlock(form) {
    const formData = new FormData(form);
    const blockId = form.querySelector('input[name="id"]').value;
    const blockType = form.querySelector('input[name="type"]').value;

    showSaveStatus(form, true);
    // Общая валидация для всех типов блоков
    if (blockType === "video") {
      const title = form.querySelector('input[name="title"]').value.trim();
      const step = form.querySelector('input[name="step"]').value.trim();

      if (!title && !step && !blockId) {
        form.closest(".card").remove();
        return;
      }
    }

    fetch(window.djangoContext.editCourseUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": form.querySelector('input[name="csrfmiddlewaretoken"]')
          .value,
      },
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showSuccessMessage("Блок успешно сохранен");
          if (blockId === "" && data.id) {
            form.querySelector('input[name="id"]').value = data.id;
            form.closest(".card").setAttribute("data-id", data.id);

            // Для тестов обновляем кнопку редактирования
            if (blockType === "test") {
              const editBtn = form.querySelector('[onclick*="openTestEditor"]');
              if (editBtn) {
                editBtn.setAttribute(
                  "onclick",
                  `Editor.openTestEditor(this.closest('.card'))`
                );
              }
            }
          }
        } else {
          showErrorMessage(data.error || "Ошибка при сохранении блока");
        }
      })
      .catch((error) => {
        showErrorMessage("Ошибка сети: " + error.message);
      });
  }

  function deleteBlock(block) {
    const blockId = block.getAttribute("data-id");

    // Проверяем, есть ли сохраненные данные или введенные значения
    const hasData =
      blockId ||
      (block.querySelector('input[name="title"]') &&
        block.querySelector('input[name="title"]').value) ||
      (block.querySelector('input[name="step"]') &&
        block.querySelector('input[name="step"]').value) ||
      (block.querySelector("trix-editor") &&
        block
          .querySelector("trix-editor")
          .editor.getDocument()
          .toString()
          .trim() !== "");

    if (!hasData) {
      // Просто удаляем блок из DOM, если он пустой
      block.remove();
      return;
    }

    // Стандартное удаление через AJAX
    const blockType = block.getAttribute("data-type");

    if (!confirm("Вы уверены, что хотите удалить этот блок?")) return;

    fetch(window.djangoContext.editCourseUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": window.djangoContext.csrfToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action: "delete",
        type: blockType,
        id: blockId,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          block.remove();
          showSuccessMessage("Блок успешно удален");
        } else {
          showErrorMessage(data.error || "Ошибка при удалении блока");
        }
      })
      .catch((error) => {
        showErrorMessage("Ошибка сети: " + error.message);
      });
  }

  // Публичные методы
  return {
    init: function () {
      // Обработчики для кнопок добавления
      document.querySelectorAll('[data-action="add-text"]').forEach((btn) => {
        btn.addEventListener("click", this.addTextBlock.bind(this));
      });

      document.querySelectorAll('[data-action="add-test"]').forEach((btn) => {
        btn.addEventListener("click", this.addTestBlock.bind(this));
      });

      document.querySelectorAll('.block-form').forEach(form => {
        // Добавляем элемент статуса сохранения
        addSaveStatus(form);

        // Обработчики изменений для текстовых полей
        form.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
          input.addEventListener('input', () => {
            showSaveStatus(form);
          });
        });

        // Обработчики изменений для Trix Editor
        if (form.querySelector('trix-editor')) {
          form.querySelector('trix-editor').addEventListener('trix-change', () => {
            showSaveStatus(form);
          });
        }
      });
      window.addEventListener('beforeunload', function(e) {
    if (hasUnsavedChanges()) {
      // Стандартный способ показать сообщение
      e.preventDefault();
      e.returnValue = 'У вас есть несохраненные изменения. Вы уверены, что хотите покинуть страницу?';
      return e.returnValue;
    }
  });
      // Обработчики для форм
      document.querySelectorAll(".block-form").forEach((form) => {
        form.addEventListener("submit", function (e) {
          e.preventDefault();
          const blockType = this.querySelector('input[name="type"]').value;

          if (blockType === "text") {
            saveBlock(this);
          } else if (blockType === "video") {
            const title = this.querySelector(
              'input[name="title"]'
            ).value.trim();
            const step = this.querySelector('input[name="step"]').value.trim();

            if (!title) {
              showErrorMessage("Введите ссылку на видео");
              return;
            }

            if (!step) {
              showErrorMessage("Укажите номер страницы");
              return;
            }

            saveBlock(this);
          }
        });
      });

      // Делегированные обработчики для вопросов и ответов
     // Внутри функции init() замените обработчики на эти:

document.addEventListener("click", (e) => {
    if (e.target.closest('[data-action="edit-test"]')) {
        e.preventDefault();
        this.openTestEditor(e.target.closest(".card"));
    } else if (e.target.closest('[data-action="remove-question"]')) {
        e.preventDefault();
        const index = e.target.closest('[data-action="remove-question"]').dataset.index;
        this.removeQuestion(index);
    } else if (e.target.closest('[data-action="add-answer"]')) {
        e.preventDefault();
        const index = e.target.closest('[data-action="add-answer"]').dataset.index;
        this.addAnswer(index);
    } else if (e.target.closest('[data-action="remove-answer"]')) {
        e.preventDefault();
        const btn = e.target.closest('[data-action="remove-answer"]');
        this.removeAnswer(btn.dataset.qindex, btn.dataset.aindex);
    } else if (e.target.closest(".correct-answer-toggle")) {
        e.preventDefault();
        const toggle = e.target.closest(".correct-answer-toggle");
        if (!toggle) return;

        const group = toggle.closest(".answer-group");
        if (!group) return;

        const radio = group.querySelector(".correct-answer");
        if (!radio) return;

        const textSpan = group.querySelector(".input-group-text");
        if (!textSpan) return;

        const qIndex = radio.dataset.qindex;
        const aIndex = radio.dataset.aindex;

        // Получаем все радио-кнопки для этого вопроса
        const allRadios = document.querySelectorAll(`input[name="${radio.name}"]`);

        // Если этот ответ уже выбран - снимаем отметку
        if (radio.checked) {
            radio.checked = false;
            textSpan.className = 'input-group-text bg-light';
            textSpan.textContent = 'Отметить правильным';

            // Обновляем данные
            questions[qIndex].answers.forEach(answer => {
                answer.is_correct = false;
            });
            return;
        }

        // Снимаем отметки со всех вариантов
        allRadios.forEach(r => {
            r.checked = false;
            const parentGroup = r.closest(".answer-group");
            if (parentGroup) {
                const parentTextSpan = parentGroup.querySelector('.input-group-text');
                if (parentTextSpan) {
                    parentTextSpan.className = 'input-group-text bg-light';
                    parentTextSpan.textContent = 'Отметить правильным';
                }
            }
        });

        // Отмечаем текущий вариант
        radio.checked = true;
        textSpan.className = 'input-group-text bg-success text-white';
        textSpan.textContent = '✓ Правильный ответ';

        // Обновляем данные
        this.updateCorrectAnswer(qIndex, aIndex);
    } else if (e.target.closest(".delete-block")) {
        e.preventDefault();
        deleteBlock(e.target.closest(".card"));
    }

     if (e.target.closest('[data-action="add-pair"]')) {
        e.preventDefault();
        const index = e.target.closest('[data-action="add-pair"]').dataset.index;
        this.addPair(index);
    } else if (e.target.closest('[data-action="remove-pair"]')) {
        e.preventDefault();
        const btn = e.target.closest('[data-action="remove-pair"]');
        this.removePair(btn.dataset.qindex, btn.dataset.pindex);
    }
});





      // Обработчики изменений
      document.addEventListener("change", (e) => {
        if (e.target.classList.contains("question-text")) {
          this.updateQuestionText(e.target.dataset.index, e.target.value);
        } else if (e.target.classList.contains("answer-text")) {
          this.updateAnswerText(
            e.target.dataset.qindex,
            e.target.dataset.aindex,
            e.target.value
          );
        } else if (
          e.target.classList.contains("correct-answer") &&
          e.target.checked
        ) {
          this.updateCorrectAnswer(
            e.target.dataset.qindex,
            e.target.dataset.aindex
          );
        }
      });

      // Инициализация Trix Editor
      document.addEventListener("focusin", function (event) {
        if (event.target.tagName === "TRIX-EDITOR") {
          const toolbarId = event.target.getAttribute("toolbar");
          const toolbar = document.getElementById(toolbarId);
          if (toolbar) toolbar.classList.add("active");
        }
      });

      document.addEventListener("input", (e) => {
    if (e.target.classList.contains("question-text")) {
        const qIndex = e.target.dataset.index;
        questions[qIndex].text = e.target.value;
    } else if (e.target.classList.contains("answer-text")) {
        const qIndex = e.target.dataset.qindex;
        const aIndex = e.target.dataset.aindex;
        questions[qIndex].answers[aIndex].text = e.target.value;
    } else if (e.target.classList.contains("correct-answer-input")) {
        const qIndex = e.target.dataset.index;
        questions[qIndex].correct_answer = e.target.value;
    }

    if (e.target.classList.contains("question-text")) {
        const qIndex = e.target.dataset.index;
        questions[qIndex].text = e.target.value;
    } else if (e.target.classList.contains("answer-text")) {
        const qIndex = e.target.dataset.qindex;
        const aIndex = e.target.dataset.aindex;
        questions[qIndex].answers[aIndex].text = e.target.value;
    } else if (e.target.classList.contains("correct-answer-input")) {
        const qIndex = e.target.dataset.index;
        questions[qIndex].correct_answer = e.target.value;
    } else if (e.target.classList.contains("term-input")) {
        const qIndex = e.target.dataset.qindex;
        const pIndex = e.target.dataset.pindex;
        this.updatePairTerm(qIndex, pIndex, e.target.value);
    } else if (e.target.classList.contains("definition-input")) {
        const qIndex = e.target.dataset.qindex;
        const pIndex = e.target.dataset.pindex;
        this.updatePairDefinition(qIndex, pIndex, e.target.value);
    }
}),

      document.addEventListener("focusout", function (event) {
        if (event.target.tagName === "TRIX-EDITOR") {
          const toolbarId = event.target.getAttribute("toolbar");
          const toolbar = document.getElementById(toolbarId);
          if (toolbar) toolbar.classList.remove("active");
        }
      });
    },


    openTestEditor: function (blockElement) {
      currentTestBlock = blockElement;
      const form = blockElement.querySelector(".block-form");
      const testId = form.querySelector('input[name="id"]').value;

      document.getElementById("testIdInput").value = testId;
      document.getElementById("testTitle").value =
        form.querySelector('input[name="title"]').value || "";
      document.getElementById("testStep").value =
        form.querySelector('input[name="step"]').value || "";

      if (testId && !testId.startsWith("new-")) {
        loadTestQuestions(testId);
      } else {
        questions = [];
        renderQuestions();
      }

      $("#testEditorModal").modal("show");
    },
    addPair: function(qIndex) {
    if (!questions[qIndex].pairs) {
        questions[qIndex].pairs = [];
    }
    questions[qIndex].pairs.push({ term: "", definition: "" });
    renderQuestions();
},

removePair: function(qIndex, pIndex) {
    questions[qIndex].pairs.splice(pIndex, 1);
    renderQuestions();
},

updatePairTerm: function(qIndex, pIndex, term) {
    questions[qIndex].pairs[pIndex].term = term;
},

updatePairDefinition: function(qIndex, pIndex, definition) {
    questions[qIndex].pairs[pIndex].definition = definition;
},

    addQuestion: function(type = 'MC') {
    const newQuestion = {
        id: null,
        text: "",
        type: type,
        answers: type === 'MC' ? [
            { id: null, text: "", is_correct: false },
            { id: null, text: "", is_correct: false }
        ] : [],
        correct_answer: type === 'FB' ? "" : null,
        pairs: type === 'MT' ? [
            { term: "", definition: "" },
            { term: "", definition: "" }
        ] : []
    };
    questions.push(newQuestion);
    renderQuestions();
},

    addAnswer: function (qIndex) {
    // Добавляем ответ только для вопросов с выбором
    if (questions[qIndex].type === 'MC') {
        questions[qIndex].answers.push({ id: null, text: "", is_correct: false });
        renderQuestions();
    }
},

    removeAnswer: function (qIndex, aIndex) {
    // Удаляем ответ только для вопросов с выбором
    if (questions[qIndex].type === 'MC') {
        questions[qIndex].answers.splice(aIndex, 1);
        renderQuestions();
    }
},

    updateQuestionText: function (qIndex, text) {
      questions[qIndex].text = text;
    },

    updateAnswerText: function (qIndex, aIndex, text) {
      questions[qIndex].answers[aIndex].text = text;
    },

    updateCorrectAnswer: function(qIndex, aIndex) {
    questions[qIndex].answers.forEach((answer, index) => {
        answer.is_correct = index === parseInt(aIndex);
    });
},

    removeQuestion: function (qIndex) {
      questions.splice(qIndex, 1);
      renderQuestions();
    },

    saveTest: function () {
      const testId = document.getElementById("testIdInput").value;
      const title = document.getElementById("testTitle").value.trim();
      const step = document.getElementById("testStep").value;

      // Валидация
      if (!title) {
        showErrorMessage("Введите название теста");
        return;
      }

      if (!step || isNaN(step)) {
        showErrorMessage("Номер страницы должен быть числом");
        return;
      }

      // Проверка вопросов
      if (questions.length === 0) {
        showErrorMessage("Добавьте хотя бы один вопрос");
        return;
      }

      // Проверка каждого вопроса
      for (const question of questions) {
    if (!question.text.trim()) {
        showErrorMessage("Все вопросы должны содержать текст");
        return;
    }

    if (question.type === 'MC') {
        const validAnswers = question.answers.filter(a => a.text.trim());
        if (validAnswers.length < 2) {
            showErrorMessage("Каждый вопрос с выбором должен иметь минимум 2 ответа");
            return;
        }

        const correctAnswers = validAnswers.filter(a => a.is_correct);
        if (correctAnswers.length !== 1) {
            showErrorMessage("Каждый вопрос с выбором должен иметь ровно 1 правильный ответ");
            return;
        }
    } else if (question.type === 'FB') {
        if (!question.correct_answer || !question.correct_answer.trim()) {
            showErrorMessage("Для вопросов на дополнение укажите правильный ответ");
            return;
        }
    }
}

      // Подготовка данных
      const formData = new FormData();
      formData.append("type", "test");
      formData.append("id", testId);
      formData.append("title", title);
      formData.append("step", step);
      formData.append("questions", JSON.stringify(questions));

      // Отправка на сервер
      fetch(window.djangoContext.editCourseUrl, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": window.djangoContext.csrfToken,
        },
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            showSuccessMessage("Тест успешно сохранен");

            if (currentTestBlock) {
              const form = currentTestBlock.querySelector(".block-form");
              form.querySelector('input[name="id"]').value = data.id;
              form.querySelector('input[name="title"]').value = title;
              form.querySelector('input[name="step"]').value = step;
              currentTestBlock.setAttribute("data-id", data.id);
            }

            $("#testEditorModal").modal("hide");
          } else {
            throw new Error(data.error || "Ошибка сохранения теста");
          }
        })
        .catch((error) => {
          showErrorMessage(error.message);
          console.error("Ошибка:", error);
        });
    },

    addTextBlock: function (e) {
      if (e) e.preventDefault();

      textBlockCounter++;
      const container = document.getElementById("blocks-container");
      const editorId = `editor-new-${textBlockCounter}`;
      const toolbarId = `toolbar-new-${textBlockCounter}`;

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

          <div class="form-group">
            <input name="step" class="typeahead tt-input" type="number" placeholder="Введите номер страницы">
          </div>
        </form>
      </div>
    </div>
  `;

      container.insertAdjacentHTML("beforeend", textBlock);
      container.lastElementChild.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });

      const newForm = container.lastElementChild.querySelector(".block-form");
      newForm.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
    input.addEventListener('input', () => {
      const statusElement = newForm.querySelector('.save-status');
      if (statusElement) {
        statusElement.classList.remove('hidden');
      }
    });
  });
if (newForm.querySelector('trix-editor')) {
    newForm.querySelector('trix-editor').addEventListener('trix-change', () => {
      const statusElement = newForm.querySelector('.save-status');
      if (statusElement) {
        statusElement.classList.remove('hidden');
      }
    });
  }

      newForm.addEventListener("submit", function (e) {
        e.preventDefault();
        saveBlock(this);
      });

      container.lastElementChild
        .querySelector(".delete-block")
        .addEventListener("click", function () {
          deleteBlock(this.closest(".card"));
        });
    },

    addVideoBlock: function (e) {
      if (e) e.preventDefault();

      const container = document.getElementById("blocks-container");

      const videoBlock = `
    <div class="card mb-3" data-type="video">
      <div class="card-body">
        <form class="block-form" method="post" enctype="multipart/form-data">
          <input type="hidden" name="csrfmiddlewaretoken" value="${window.djangoContext.csrfToken}">
          <input type="hidden" name="type" value="video">
          <input type="hidden" name="id" value="">
          <div style="margin-left: -15px;" class="form-group d-flex align-items-center justify-content-between">
            <label style="border: none; font-size: 20px; font-weight: normal;" class="form-control me-3">Видео</label>
            <div class="d-flex gap-3 align-items-center justify-content-center">
              <h6 class="card-description mb-0 d-flex save-status hidden">Несохранено</h6>
              <button type="submit" style="margin: 5px" class="btn btn-outline-primary">Сохранить</button>
              <button type="button" class="btn btn-inverse-danger btn-icon delete-block">
                <i class="ti-close"></i>
              </button>
            </div>
          </div>
          <div class="form-group row">
            <label for="exampleInputUrl" class="col-sm-3 col-form-label">Ссылка</label>
            <div class="col-sm-9">
              <input name="title" type="text" class="form-control" id="exampleInputUrl"
                  placeholder="Введите ссылку на видео из VK">
            </div>
          </div>
          <div class="form-group">
            <input name="step" class="typeahead tt-input" type="number" placeholder="Номер страницы">
          </div>
        </form>
      </div>
    </div>
  `;

      container.insertAdjacentHTML("beforeend", videoBlock);
      container.lastElementChild.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });

      const newForm = container.lastElementChild.querySelector(".block-form");
      newForm.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
    input.addEventListener('input', () => {
      const statusElement = newForm.querySelector('.save-status');
      if (statusElement) {
        statusElement.classList.remove('hidden');
      }
    });
  });

      newForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const titleInput = this.querySelector('input[name="title"]');
        const stepInput = this.querySelector('input[name="step"]');

        // Проверка на пустые поля перед сохранением
        if (!titleInput.value.trim() || !stepInput.value.trim()) {
          showErrorMessage("Заполните все обязательные поля");
          return;
        }

        saveBlock(this);
      });

      container.lastElementChild
        .querySelector(".delete-block")
        .addEventListener("click", function () {
          const block = this.closest(".card");
          if (
            !block.getAttribute("data-id") &&
            !block.querySelector('input[name="title"]').value.trim() &&
            !block.querySelector('input[name="step"]').value.trim()
          ) {
            // Удаляем только если блок новый и пустой
            block.remove();
          } else {
            // Стандартное удаление с подтверждением
            deleteBlock(block);
          }
        });
    },

    addTestBlock: function (e) {
      if (e) e.preventDefault();

      const container = document.getElementById("blocks-container");
      const testId = "new-" + Date.now();

      const testBlock = `
                <div class="card mb-3" data-id="${testId}" data-type="test">
                    <div class="card-body">
                        <form class="block-form" method="post" enctype="multipart/form-data">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${window.djangoContext.csrfToken}">
                            <input type="hidden" name="type" value="test">
                            <input type="hidden" name="id" value="">
                            <div style="margin-left: -15px;" class="form-group d-flex align-items-center justify-content-between mt-2">
                                <input name="title" style="border: none; font-size: 20px; font-weight: normal;"
                                       type="text" class="form-control me-3" placeholder="Введите название теста...">
                                <div class="d-flex gap-3 align-items-center justify-content-center">
                                    <button type="button" style="margin: 5px" class="btn btn-outline-primary"
                                            data-action="edit-test">
                                        Редактировать
                                    </button>
                                    <button type="button" class="btn btn-inverse-danger btn-icon delete-block">
                                        <i class="ti-close"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="form-group">
                                <input name="step" class="typeahead tt-input" type="number" placeholder="Введите номер страницы">
                            </div>
                        </form>
                    </div>
                </div>
            `;

      container.insertAdjacentHTML("beforeend", testBlock);
      container.lastElementChild.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });

      container.lastElementChild
        .querySelector(".delete-block")
        .addEventListener("click", function () {
          deleteBlock(this.closest(".card"));
        });
    },
  };
})();
// Инициализация после загрузки DOM
document.addEventListener("DOMContentLoaded", function () {
  Editor.init();
});
