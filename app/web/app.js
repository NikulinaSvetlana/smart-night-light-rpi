/*
  Фронтенд управления ночником (vanilla JS, без сборки).

  - Хранит API-токен в localStorage.
  - Управляет LED через FastAPI (/api/v1/...).
  - Визуально эмулирует яркость LED (круг-«лампа» на экране).
  - Работает на телефоне через Wi-Fi (мобильный браузер).
*/

const $ = (id) => document.getElementById(id);

/* ── Токен ── */

function getToken() {
  return localStorage.getItem("nightlight_api_token") || "";
}

function setToken(value) {
  localStorage.setItem("nightlight_api_token", value);
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/* ── API ── */

async function api(path, options = {}) {
  const resp = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status}: ${text}`);
  }
  return resp.json();
}

async function setPower(isOn) {
  return api("/api/v1/devices/nightlight/power", {
    method: "POST",
    body: JSON.stringify({ is_on: isOn }),
  });
}

async function setBrightness(val) {
  return api("/api/v1/devices/nightlight/brightness", {
    method: "POST",
    body: JSON.stringify({ brightness: val }),
  });
}

async function getState() {
  return api("/api/v1/devices/nightlight/state", { method: "GET" });
}

/* ── UI: визуальный эмулятор лампы ── */

function updateLamp(isOn, brightness) {
  const lamp = $("lamp");
  const label = $("lampLabel");
  const b = isOn ? brightness : 0;

  // Плавно меняем прозрачность и свечение круга-«лампы»
  lamp.style.opacity = String(0.06 + b * 0.94);
  lamp.style.boxShadow =
    b > 0
      ? `0 0 ${b * 70}px ${b * 25}px rgba(251,191,36,${b * 0.6})`
      : "0 0 0 0 transparent";

  label.textContent = isOn ? `${Math.round(brightness * 100)}%` : "ВЫКЛ";
}

function updateButtons(isOn) {
  $("btnOn").classList.toggle("active", isOn);
  $("btnOff").classList.toggle("active", !isOn);
}

function updateSliderTrack(slider) {
  const pct = slider.value;
  slider.style.background =
    `linear-gradient(to right, #fbbf24 0%, #fbbf24 ${pct}%, #1f2937 ${pct}%)`;
}

function renderState(state) {
  const brightness = state.brightness || 0;
  const percent = Math.round(brightness * 100);

  const slider = $("brightness");
  slider.value = String(percent);
  $("brightnessValue").textContent = `${percent}%`;
  updateSliderTrack(slider);

  $("status").textContent = JSON.stringify(state, null, 2);

  updateLamp(state.is_on, brightness);
  updateButtons(state.is_on);
  setConn("ok");
}

/* ── Индикатор подключения ── */

function setConn(status) {
  const dot = $("connStatus");
  dot.classList.remove("ok", "err");
  dot.classList.add(status);
}

/* ── Безопасный вызов API с обработкой ошибок ── */

async function safeCall(fn) {
  try {
    return await fn();
  } catch (e) {
    setConn("err");
    $("status").textContent = e.message;
    return null;
  }
}

/* ── Привязка событий ── */

function wire() {
  // Токен
  const tokenInput = $("token");
  tokenInput.value = getToken();
  $("saveToken").addEventListener("click", () => {
    setToken(tokenInput.value.trim());
  });

  // Питание
  $("btnOn").addEventListener("click", () =>
    safeCall(async () => renderState(await setPower(true)))
  );
  $("btnOff").addEventListener("click", () =>
    safeCall(async () => renderState(await setPower(false)))
  );

  // Ползунок яркости
  const slider = $("brightness");

  slider.addEventListener("input", () => {
    const pct = Number(slider.value);
    $("brightnessValue").textContent = `${pct}%`;
    updateSliderTrack(slider);
    // Превью лампы в реальном времени при перетаскивании
    updateLamp(pct > 0, pct / 100);
  });

  slider.addEventListener("change", () =>
    safeCall(async () => {
      const value = Number(slider.value) / 100;
      renderState(await setBrightness(value));
    })
  );

  // Обновить
  $("refresh").addEventListener("click", () =>
    safeCall(async () => renderState(await getState()))
  );

  // Загрузить текущее состояние при открытии страницы
  safeCall(async () => renderState(await getState()));
}

wire();
