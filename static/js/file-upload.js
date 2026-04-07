// Функции для уведомлений
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

// Обработчики для кнопок сохранения/удаления
function setupActionButtons() {
  // Кнопка "Сохранить"
  const saveButton = document.getElementById('saveButton');
  if (saveButton) {
    saveButton.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Собираем данные формы
      const form = document.querySelector('form.forms-sample');
      const formData = new FormData(form);
      
      // Отправляем AJAX запрос
      fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        }
      })
      .then(response => {
        if (response.ok) {
          return response.text();
        }
        throw new Error('Ошибка сохранения');
      })
      .then(() => {
        showSuccessMessage('Изменения успешно сохранены!');
      })
      .catch(error => {
        showErrorMessage(error.message);
      });
    });
  }
  
  // Кнопка "Удалить"
  const deleteButton = document.getElementById('deleteButton');
  if (deleteButton) {
    deleteButton.addEventListener('click', function(e) {
      e.preventDefault();
      // Имитируем клик по кнопке, которая открывает модальное окно удаления
      const deleteTrigger = document.querySelector('button[data-target="#deleteModal"]');
      if (deleteTrigger) {
        deleteTrigger.click();
      }
    });
  }
}

// Инициализация загрузки файлов
function setupFileUpload() {
  const uploadBtn = document.getElementById('uploadBtn');
  const imageInput = document.getElementById('imageInput');
  const filePathDisplay = document.getElementById('filePathDisplay');
  const previewImage = document.getElementById('previewImage');

  if (uploadBtn && imageInput) {
    // Нажатие на кнопку "Upload" → клик по input file
    uploadBtn.addEventListener('click', () => {
      imageInput.click();
    });

    // При выборе нового файла
    imageInput.addEventListener('change', () => {
      const file = imageInput.files[0];
      if (file) {
        // Показать путь к файлу
        if (filePathDisplay) {
          filePathDisplay.value = file.name;
        }

        // Показать превью изображения
        if (previewImage) {
          const reader = new FileReader();
          reader.onload = (e) => {
            previewImage.src = e.target.result;
          };
          reader.readAsDataURL(file);
        }
      }
    }),
    // Отмена всплывающего окна при клике на загрузку
    (e) => {
      e.preventDefault();
      e.stopPropagation();
    },
    false;
  }
}

// Главная функция инициализации
document.addEventListener('DOMContentLoaded', function() {
  // Создаем область для уведомлений, если её нет
  if (!document.getElementById('notification-area')) {
    const notificationArea = document.createElement('div');
    notificationArea.id = 'notification-area';
    notificationArea.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; width: 300px;';
    document.body.insertBefore(notificationArea, document.body.firstChild);
  }

  // Инициализируем функционал
  setupFileUpload();
  setupActionButtons();
});
