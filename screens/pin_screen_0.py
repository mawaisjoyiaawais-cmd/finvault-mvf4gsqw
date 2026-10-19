from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.app import App

from storage import is_pin_configured, verify_pin, set_new_pin, reset_all_data
from ui import (
    RoundedButton,
    show_confirm,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_EXPENSE,
    COLOR_MUTED,
)


class VaultLogo(Widget):
    """Canvas-drawn geometric wallet shield icon."""
    def __init__(self, **kwargs):
        super(VaultLogo, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (64, 64)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Shield/wallet body
            Color(0.063, 0.725, 0.506, 0.18)
            Ellipse(pos=(self.x - 4, self.y - 4), size=(self.width + 8, self.height + 8))
            Color(0.063, 0.725, 0.506, 1.0)
            RoundedRectangle(pos=(self.x + 8, self.y + 6), size=(self.width - 16, self.height - 14), radius=[14, 14, 14, 14])
            # Inner geometric clasp
            Color(0.059, 0.090, 0.165, 1.0)
            RoundedRectangle(pos=(self.x + 18, self.y + 16), size=(self.width - 36, self.height - 34), radius=[8, 8, 8, 8])
            # Spark / Lock center accent
            Color(0.063, 0.725, 0.506, 1.0)
            Ellipse(pos=(self.x + self.width / 2 - 5, self.y + self.height / 2 - 5), size=(10, 10))


class PinDot(Widget):
    """Individual slot indicator for PIN digits."""
    def __init__(self, **kwargs):
        super(PinDot, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (20, 20)
        self._filled = False
        self._error = False
        self.bind(pos=self._redraw, size=self._redraw)

    def set_state(self, filled=False, error=False):
        self._filled = filled
        self._error = error
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            if self._error:
                Color(*COLOR_EXPENSE)
                Ellipse(pos=self.pos, size=self.size)
            elif self._filled:
                Color(*COLOR_PRIMARY)
                Ellipse(pos=self.pos, size=self.size)
            else:
                Color(*COLOR_CARD_LIGHT)
                Ellipse(pos=self.pos, size=self.size)
                Color(*COLOR_MUTED)
                Line(circle=(self.x + self.width / 2, self.y + self.height / 2, self.width / 2), width=1.4)


class PinScreenScreen0(Screen):
    def __init__(self, **kwargs):
        super(PinScreenScreen0, self).__init__(**kwargs)
        self.current_pin = ""
        self.is_setup_mode = False
        self.setup_step = 1
        self.first_entered_pin = ""
        self.dots = []

        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[24, 20, 24, 16], spacing=10)

        # Top branding & logo
        top_box = BoxLayout(orientation="vertical", size_hint_y=None, height=130, spacing=6, padding=[0, 10, 0, 0])
        
        logo_container = BoxLayout(size_hint_y=None, height=64)
        logo_container.add_widget(Widget(size_hint_x=1))
        self.logo = VaultLogo()
        logo_container.add_widget(self.logo)
        logo_container.add_widget(Widget(size_hint_x=1))
        top_box.add_widget(logo_container)

        self.app_title = Label(
            text="FinVault",
            font_size="22sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=28,
            halign="center"
        )
        self.app_title.bind(size=self.app_title.setter("text_size"))
        top_box.add_widget(self.app_title)

        self.instruction_label = Label(
            text="Enter your 4-digit PIN",
            font_size="14sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=22,
            halign="center"
        )
        self.instruction_label.bind(size=self.instruction_label.setter("text_size"))
        top_box.add_widget(self.instruction_label)
        root.add_widget(top_box)

        # Dots indicator row
        self.dots_container = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            size=(140, 28),
            spacing=16,
            pos_hint={"center_x": 0.5}
        )
        for _ in range(4):
            dot = PinDot()
            self.dots.append(dot)
            self.dots_container.add_widget(dot)
        root.add_widget(self.dots_container)

        # Feedback / error message
        self.error_label = Label(
            text="",
            font_size="13sp",
            color=COLOR_EXPENSE,
            size_hint_y=None,
            height=24,
            halign="center"
        )
        self.error_label.bind(size=self.error_label.setter("text_size"))
        root.add_widget(self.error_label)

        # Numeric Keypad Grid
        keypad = GridLayout(cols=3, spacing=12, padding=[10, 4, 10, 4], size_hint_y=1)
        keys = [
            "1", "2", "3",
            "4", "5", "6",
            "7", "8", "9",
            "C", "0", "DEL"
        ]
        for key in keys:
            if key == "C":
                btn = RoundedButton(
                    text="C",
                    font_size="18sp",
                    bold=True,
                    bg_color=COLOR_CARD_LIGHT,
                    text_color=COLOR_TEXT_SECONDARY,
                    radius=[16, 16, 16, 16]
                )
                btn.bind(on_release=lambda inst: self._on_clear())
            elif key == "DEL":
                btn = RoundedButton(
                    text="<-",
                    font_size="18sp",
                    bold=True,
                    bg_color=COLOR_CARD_LIGHT,
                    text_color=COLOR_TEXT_SECONDARY,
                    radius=[16, 16, 16, 16]
                )
                btn.bind(on_release=lambda inst: self._on_backspace())
            else:
                btn = RoundedButton(
                    text=key,
                    font_size="22sp",
                    bold=True,
                    bg_color=COLOR_CARD,
                    text_color=COLOR_TEXT_PRIMARY,
                    radius=[16, 16, 16, 16]
                )
                btn.bind(on_release=lambda inst, k=key: self._on_digit_press(k))
            keypad.add_widget(btn)
        root.add_widget(keypad)

        # Forgot / Reset hint
        bottom_bar = BoxLayout(size_hint_y=None, height=36, spacing=8)
        self.forgot_btn = RoundedButton(
            text="Forgot PIN / Reset",
            font_size="12sp",
            bg_color=(0, 0, 0, 0),
            text_color=COLOR_TEXT_SECONDARY,
            size_hint=(1, 1)
        )
        self.forgot_btn.bind(on_release=lambda inst: self._on_forgot_pin())
        bottom_bar.add_widget(self.forgot_btn)
        root.add_widget(bottom_bar)

        self.add_widget(root)

    def on_pre_enter(self):
        """Check PIN existence and set initial state."""
        self.current_pin = ""
        self.error_label.text = ""
        self._update_dots_view(error=False)

        configured = is_pin_configured()
        if not configured:
            self.is_setup_mode = True
            self.setup_step = 1
            self.first_entered_pin = ""
            self.app_title.text = "Welcome to FinVault"
            self.instruction_label.text = "Create a new 4-digit master PIN"
            self.forgot_btn.opacity = 0
            self.forgot_btn.disabled = True
        else:
            self.is_setup_mode = False
            self.setup_step = 1
            self.first_entered_pin = ""
            self.app_title.text = "FinVault Locked"
            self.instruction_label.text = "Enter your 4-digit PIN"
            self.forgot_btn.opacity = 1
            self.forgot_btn.disabled = False

    def _on_digit_press(self, digit_str):
        if len(self.current_pin) < 4:
            self.current_pin += str(digit_str)
            self.error_label.text = ""
            self._update_dots_view(error=False)

            if len(self.current_pin) == 4:
                Clock.schedule_once(self._verify_or_process_pin, 0.12)

    def _on_backspace(self):
        if self.current_pin:
            self.current_pin = self.current_pin[:-1]
            self.error_label.text = ""
            self._update_dots_view(error=False)

    def _on_clear(self):
        self.current_pin = ""
        self.error_label.text = ""
        self._update_dots_view(error=False)

    def _update_dots_view(self, error=False):
        filled_count = len(self.current_pin)
        for i, dot in enumerate(self.dots):
            dot.set_state(filled=(i < filled_count), error=error)

    def _shake_dots(self):
        orig_x = self.dots_container.x
        anim = (
            Animation(x=orig_x - 14, duration=0.04)
            + Animation(x=orig_x + 14, duration=0.04)
            + Animation(x=orig_x - 8, duration=0.04)
            + Animation(x=orig_x + 8, duration=0.04)
            + Animation(x=orig_x, duration=0.04)
        )
        anim.start(self.dots_container)

    def _verify_or_process_pin(self, dt=0):
        if self.is_setup_mode:
            if self.setup_step == 1:
                self.first_entered_pin = self.current_pin
                self.current_pin = ""
                self.setup_step = 2
                self.instruction_label.text = "Re-enter PIN to confirm"
                self.error_label.text = ""
                self._update_dots_view(error=False)
            else:
                if self.current_pin == self.first_entered_pin:
                    set_new_pin(self.current_pin)
                    self.is_setup_mode = False
                    self.current_pin = ""
                    self._update_dots_view(error=False)
                    app = App.get_running_app()
                    if app and hasattr(app, "go"):
                        app.go("dashboard_screen_1")
                else:
                    self._shake_dots()
                    self.error_label.text = "PIN mismatch! Let's start over."
                    self._update_dots_view(error=True)
                    self.setup_step = 1
                    self.first_entered_pin = ""
                    self.current_pin = ""
                    self.instruction_label.text = "Create a new 4-digit PIN"
                    Clock.schedule_once(lambda dt: self._update_dots_view(error=False), 0.5)
        else:
            if verify_pin(self.current_pin):
                self.current_pin = ""
                self.error_label.text = ""
                self._update_dots_view(error=False)
                app = App.get_running_app()
                if app and hasattr(app, "go"):
                    app.go("dashboard_screen_1")
            else:
                self._shake_dots()
                self.error_label.text = "Incorrect PIN. Please try again."
                self._update_dots_view(error=True)
                self.current_pin = ""
                Clock.schedule_once(lambda dt: self._update_dots_view(error=False), 0.5)

    def _on_forgot_pin(self):
        def on_confirm_reset():
            reset_all_data()
            self.on_pre_enter()

        show_confirm(
            "Reset Security PIN",
            "Forgot your PIN?\nResetting will erase all local transactions and goals to ensure security. Are you sure?",
            on_confirm=on_confirm_reset
        )
