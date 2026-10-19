from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.app import App

# Theme Palette (Emerald Green, Slate Navy, White, Alert Coral)
COLOR_PRIMARY = (0.063, 0.725, 0.506, 1.0)       # #10B981 Emerald
COLOR_PRIMARY_DARK = (0.024, 0.584, 0.404, 1.0)  # Darker Emerald
COLOR_BG = (0.059, 0.090, 0.165, 1.0)            # #0F172A Deep Slate
COLOR_CARD = (0.118, 0.161, 0.231, 1.0)          # #1E293B Card Slate
COLOR_CARD_LIGHT = (0.200, 0.255, 0.353, 1.0)    # Slightly lighter Slate
COLOR_TEXT_PRIMARY = (0.949, 0.961, 0.980, 1.0)  # Near white
COLOR_TEXT_SECONDARY = (0.580, 0.639, 0.722, 1.0)# Subtle grayish
COLOR_INCOME = (0.133, 0.773, 0.369, 1.0)        # Green #22C55E
COLOR_EXPENSE = (0.937, 0.267, 0.267, 1.0)       # Red #EF4444
COLOR_ACCENT = (0.231, 0.510, 0.965, 1.0)        # Indigo Accent #3B82F6
COLOR_MUTED = (0.298, 0.357, 0.455, 1.0)


class RoundedButton(Button):
    def __init__(self, bg_color=None, text_color=None, radius=None, **kwargs):
        super(RoundedButton, self).__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.bg_color = bg_color if bg_color is not None else COLOR_PRIMARY
        self.text_color = text_color if text_color is not None else (1, 1, 1, 1)
        self.color = self.text_color
        self.radius = radius if radius is not None else [12, 12, 12, 12]
        self.bind(pos=self._update_canvas, size=self._update_canvas, state=self._update_canvas)

    def set_bg_color(self, color):
        self.bg_color = color
        self._update_canvas()

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == "down":
                r, g, b, a = self.bg_color
                Color(max(0.0, r - 0.15), max(0.0, g - 0.15), max(0.0, b - 0.15), a)
            else:
                Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)


class Card(BoxLayout):
    def __init__(self, bg_color=None, radius=None, border_color=None, **kwargs):
        super(Card, self).__init__(**kwargs)
        self.bg_color = bg_color if bg_color is not None else COLOR_CARD
        self.radius = radius if radius is not None else [14, 14, 14, 14]
        self.border_color = border_color
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            if self.border_color:
                Color(*self.border_color)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius[0]), width=1.1)


class Header(BoxLayout):
    def __init__(self, title="FinVault", show_back=False, right_widget=None, **kwargs):
        super(Header, self).__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 60
        self.padding = [12, 8, 12, 8]
        self.spacing = 10

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        if show_back:
            back_btn = RoundedButton(
                text="< Back",
                bg_color=COLOR_CARD_LIGHT,
                size_hint=(None, 1),
                width=75,
                font_size="14sp"
            )
            back_btn.bind(on_release=lambda instance: self._on_back())
            self.add_widget(back_btn)

        self.title_label = Label(
            text=title,
            font_size="19sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left" if show_back or right_widget else "center",
            valign="middle"
        )
        self.title_label.bind(size=self.title_label.setter("text_size"))
        self.add_widget(self.title_label)

        if right_widget:
            self.add_widget(right_widget)

    def _on_back(self):
        app = App.get_running_app()
        if app and hasattr(app, "go_back"):
            app.go_back()

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLOR_BG)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
            Color(0.18, 0.24, 0.33, 0.6)
            Line(points=[self.x, self.y, self.right, self.y], width=1)


class LabeledInput(BoxLayout):
    def __init__(self, label_text="", hint_text="", is_password=False, input_filter=None, **kwargs):
        super(LabeledInput, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = 76
        self.spacing = 4

        self.label = Label(
            text=label_text,
            font_size="13sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        self.label.bind(size=self.label.setter("text_size"))
        self.add_widget(self.label)

        self.text_input = TextInput(
            hint_text=hint_text,
            password=is_password,
            input_filter=input_filter,
            multiline=False,
            size_hint_y=None,
            height=44,
            background_normal="",
            background_active="",
            background_color=COLOR_CARD,
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_MUTED,
            padding=[12, 12, 12, 12],
            font_size="15sp"
        )
        self.add_widget(self.text_input)

    @property
    def text(self):
        return self.text_input.text

    @text.setter
    def text(self, val):
        self.text_input.text = str(val)


class BottomNavBar(BoxLayout):
    """Reusable persistent bottom navigation dock across unlocked screens."""
    def __init__(self, active_route="dashboard_screen_1", **kwargs):
        super(BottomNavBar, self).__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 56
        self.padding = [4, 4, 4, 4]
        self.spacing = 4

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        tabs = [
            ("Home", "dashboard_screen_1"),
            ("History", "transaction_history_screen_3"),
            ("Reports", "reports_screen_4"),
            ("Goals", "savings_goals_screen_5"),
            ("Settings", "settings_screen_7"),
        ]

        for title, route in tabs:
            is_active = (route == active_route)
            btn = RoundedButton(
                text=title,
                font_size="12sp",
                bg_color=COLOR_PRIMARY if is_active else (0.13, 0.18, 0.26, 0.9),
                text_color=(1, 1, 1, 1) if is_active else COLOR_TEXT_SECONDARY,
                radius=[10, 10, 10, 10]
            )
            btn.bind(on_release=lambda inst, r=route: self._nav_to(r))
            self.add_widget(btn)

    def _nav_to(self, route):
        app = App.get_running_app()
        if app and hasattr(app, "go"):
            app.go(route)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.08, 0.12, 0.20, 1.0)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
            Color(0.18, 0.24, 0.33, 0.8)
            Line(points=[self.x, self.top, self.right, self.top], width=1.2)


def show_message(title, text, on_dismiss=None):
    content = BoxLayout(orientation="vertical", spacing=14, padding=16)
    lbl = Label(
        text=text,
        font_size="14sp",
        color=COLOR_TEXT_PRIMARY,
        halign="center",
        valign="middle"
    )
    lbl.bind(size=lbl.setter("text_size"))
    content.add_widget(lbl)

    popup = Popup(
        title=title,
        title_size="16sp",
        title_color=COLOR_TEXT_PRIMARY,
        content=content,
        size_hint=(0.84, 0.35),
        auto_dismiss=False,
        separator_color=COLOR_PRIMARY
    )

    def _dismiss(inst):
        popup.dismiss()
        if on_dismiss:
            on_dismiss()

    ok_btn = RoundedButton(text="OK", size_hint=(1, None), height=44, bg_color=COLOR_PRIMARY)
    ok_btn.bind(on_release=_dismiss)
    content.add_widget(ok_btn)
    popup.open()


def show_confirm(title, text, on_confirm=None, on_cancel=None):
    content = BoxLayout(orientation="vertical", spacing=14, padding=16)
    lbl = Label(
        text=text,
        font_size="14sp",
        color=COLOR_TEXT_PRIMARY,
        halign="center",
        valign="middle"
    )
    lbl.bind(size=lbl.setter("text_size"))
    content.add_widget(lbl)

    btn_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=44)
    popup = Popup(
        title=title,
        title_size="16sp",
        title_color=COLOR_TEXT_PRIMARY,
        content=content,
        size_hint=(0.86, 0.38),
        auto_dismiss=False,
        separator_color=COLOR_EXPENSE
    )

    def _cancel(inst):
        popup.dismiss()
        if on_cancel:
            on_cancel()

    def _confirm(inst):
        popup.dismiss()
        if on_confirm:
            on_confirm()

    c_btn = RoundedButton(text="Cancel", bg_color=COLOR_CARD_LIGHT)
    c_btn.bind(on_release=_cancel)
    btn_row.add_widget(c_btn)

    ok_btn = RoundedButton(text="Confirm", bg_color=COLOR_EXPENSE)
    ok_btn.bind(on_release=_confirm)
    btn_row.add_widget(ok_btn)

    content.add_widget(btn_row)
    popup.open()
