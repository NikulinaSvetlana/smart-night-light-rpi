/*
  Минимальный фронтенд без сборки (vanilla JS).

  Задача этой страницы:
  - хранить API токен в localStorage,
  - отправлять команды в FastAPI (/api/v1/...),
  - отображать текущее состояние ночника (JSON) для отладки.

  Почему без фреймворков:
  - MVP должен запускаться “из коробки” без npm/yarn,
  - статика раздаётся прямо FastAPI (см. app/api/factory.py),
  - код легко читать и быстро править на Raspberry Pi.
*/

function getToken() {
  // Токен лежит в localStorage, чтобы не вводить его каждый раз после обновления страницы.
  return localStorage.getItem("nightlight_api_token") || "";
}

function setToken(value) {
  // Сохраняем токен под фиксированным ключом.
  localStorage.setItem("nightlight_api_token", value);
}

function authHeaders() {
  // Если токен задан — добавляем Authorization, иначе оставляем заголовки пустыми.
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function api(path, options) {
  // Унифицированный helper для запросов к API:
  // - выставляет JSON Content-Type,
  // - подмешивает Authorization,
  // - превращает не-2xx ответы в понятное исключение.
  const resp = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(options?.headers || {}) },
  });

  if (!resp.ok) {
    // Сервер мог вернуть JSON или текст — для простоты читаем как текст.
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }

  // Все наши ручки возвращают JSON.
  return resp.json();
}

async function setPower(isOn) {
  // Команда питания: true => включить, false => выключить.
  return api(`/api/v1/devices/nightlight/power`, {
    method: "POST",
    body: JSON.stringify({ is_on: isOn }),
  });
}

async function setBrightness(brightness01) {
  // Команда яркости принимает 0..1, поэтому UI переводит проценты в долю.
  return api(`/api/v1/devices/nightlight/brightness`, {
    method: "POST",
    body: JSON.stringify({ brightness: brightness01 }),
  });
}

async function getState() {
  // Текущее состояние устройства.
  return api(`/api/v1/devices/nightlight/state`, { method: "GET" });
}

function renderState(state) {
  // Отрисовка состояния:
  // - диапазон яркости 0..1 переводим в проценты для range input,
  // - JSON выводим как “сырой” текст для удобной диагностики.
  const percent = Math.round((state.brightness || 0) * 100);
  document.getElementById("brightness").value = String(percent);
  document.getElementById("brightnessValue").textContent = `${percent}%`;
  document.getElementById("status").textContent = JSON.stringify(state, null, 2);
}

function wire() {
  // Привязка DOM-элементов к обработчикам событий.
  const tokenInput = document.getElementById("token");
  tokenInput.value = getToken();

  document.getElementById("saveToken").addEventListener("click", () => {
    // Храним токен “как есть”, но убираем лишние пробелы по краям.
    setToken(tokenInput.value.trim());
  });

  document.getElementById("btnOn").addEventListener("click", async () => {
    // Включаем и сразу отображаем новое состояние, которое вернуло API.
    renderState(await setPower(true));
  });

  document.getElementById("btnOff").addEventListener("click", async () => {
    // Выключаем и отображаем новое состояние.
    renderState(await setPower(false));
  });

  const brightness = document.getElementById("brightness");
  brightness.addEventListener("input", () => {
    // input — частое событие при движении ползунка, поэтому тут только UI-обновление.
    document.getElementById("brightnessValue").textContent = `${brightness.value}%`;
  });
  brightness.addEventListener("change", async () => {
    // change — срабатывает после отпускания ползунка, тут уже можно дергать API.
    const value = Number(brightness.value) / 100;
    renderState(await setBrightness(value));
  });

  document.getElementById("refresh").addEventListener("click", async () => {
    // Ручная синхронизация — полезно, если состояние поменялось из другого клиента (бот/скрипт).
    renderState(await getState());
  });
}

// Инициализация при загрузке скрипта.
wire();
