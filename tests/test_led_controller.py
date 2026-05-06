"""Unit-тесты логики LedController.

Мы тестируем контроллер отдельно от FastAPI, чтобы:
- быстро проверять бизнес-правила (clamp, включение/выключение),
- убедиться, что PWM-скважность считается правильно,
- не зависеть от сетевого стека.
"""

from __future__ import annotations

from app.gpio.led import LedController
from app.gpio.mock_gpio import MockPwmOutput


def test_led_controller_power_and_brightness() -> None:
    """Яркость должна отражаться в duty_cycle, а выключение должно сбрасывать PWM."""
    pwm = MockPwmOutput(frequency_hz=800)
    led = LedController(pwm=pwm)

    state = led.state()
    assert state.is_on is False
    assert state.brightness == 0.0

    state = led.set_brightness(0.5)
    assert state.is_on is True
    assert state.brightness == 0.5
    assert pwm.duty_cycle_percent == 50.0

    state = led.set_power(False)
    assert state.is_on is False
    assert state.brightness == 0.0
    assert pwm.duty_cycle_percent == 0.0


def test_led_controller_clamps_brightness() -> None:
    """Яркость должна “обрезаться” диапазоном 0..1."""
    pwm = MockPwmOutput(frequency_hz=800)
    led = LedController(pwm=pwm)

    state = led.set_brightness(10.0)
    assert state.brightness == 1.0
    assert pwm.duty_cycle_percent == 100.0

    state = led.set_brightness(-1.0)
    assert state.brightness == 0.0
    assert state.is_on is False
