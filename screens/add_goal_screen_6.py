from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

from storage import add_goal, get_settings
from ui import (
    RoundedButton,
    Card,
    Header,
    LabeledInput,
    BottomNavBar,
    show_message,
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_MUTED,
)


class AddGoalScreenScreen6(Screen):
    def __init__(self, **kwargs):
        super(AddGoalScreenScreen6, self).__init__(**kwargs)
        self.categories = [
            "Emergency",
            "Travel",
            "Vehicle",
            "Home",
            "Gadget",
            "Education",
            "Wedding",
            "Other"
        ]
        self.selected_category = "Emergency"
        self.category_buttons = {}

        self.bind(pos=self._update_bg, size=self._update_bg)
        self._build_ui()

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLOR_BG)
            RoundedRectangle(pos=self.pos, size=self.size)

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")

        # Header
        header = Header(title="New Savings Goal", show_back=True)
        root.add_widget(header)

        # Scrollable Form Content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        form_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=16,
            padding=[16, 16, 16, 20]
        )
        form_box.bind(minimum_height=form_box.setter("height"))

        # Card 1: Goal Details
        details_card = Card(
            orientation="vertical",
            size_hint_y=None,
            padding=[14, 14, 14, 14],
            spacing=10,
            bg_color=COLOR_CARD
        )
        details_card.bind(minimum_height=details_card.setter("height"))

        card_title = Label(
            text="TARGET INFORMATION",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        card_title.bind(size=card_title.setter("text_size"))
        details_card.add_widget(card_title)

        self.title_input = LabeledInput(
            label_text="Goal Title",
            hint_text="e.g. Emergency Fund, New Laptop"
        )
        details_card.add_widget(self.title_input)

        self.target_input = LabeledInput(
            label_text="Target Amount",
            hint_text="0.00",
            input_filter="float"
        )
        details_card.add_widget(self.target_input)

        self.initial_input = LabeledInput(
            label_text="Initial Saved Deposit",
            hint_text="0.00 (optional)",
            input_filter="float"
        )
        details_card.add_widget(self.initial_input)

        form_box.add_widget(details_card)

        # Card 2: Category Selector
        category_card = Card(
            orientation="vertical",
            size_hint_y=None,
            padding=[14, 14, 14, 14],
            spacing=10,
            bg_color=COLOR_CARD
        )
        category_card.bind(minimum_height=category_card.setter("height"))

        cat_title = Label(
            text="GOAL CATEGORY",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        cat_title.bind(size=cat_title.setter("text_size"))
        category_card.add_widget(cat_title)

        cat_grid = GridLayout(cols=4, spacing=8, size_hint_y=None, height=84)
        for cat in self.categories:
            is_active = (cat == self.selected_category)
            btn = RoundedButton(
                text=cat,
                font_size="11sp",
                bg_color=COLOR_PRIMARY if is_active else COLOR_CARD_LIGHT,
                text_color=(1, 1, 1, 1) if is_active else COLOR_TEXT_SECONDARY,
                radius=[8, 8, 8, 8]
            )
            btn.bind(on_release=lambda inst, c=cat: self._select_category(c))
            self.category_buttons[cat] = btn
            cat_grid.add_widget(btn)

        category_card.add_widget(cat_grid)
        form_box.add_widget(category_card)

        # Card 3: Target Completion Date
        date_card = Card(
            orientation="vertical",
            size_hint_y=None,
            padding=[14, 14, 14, 14],
            spacing=10,
            bg_color=COLOR_CARD
        )
        date_card.bind(minimum_height=date_card.setter("height"))

        date_title = Label(
            text="TARGET COMPLETION DATE",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        date_title.bind(size=date_title.setter("text_size"))
        date_card.add_widget(date_title)

        self.date_input = LabeledInput(
            label_text="Target Date (YYYY-MM-DD)",
            hint_text="2025-12-31"
        )
        date_card.add_widget(self.date_input)

        # Quick timeframe selection buttons
        quick_dates = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=36)
        presets = [("+3 Mo", 90), ("+6 Mo", 180), ("+1 Yr", 365), ("+2 Yr", 730)]
        for label_text, days in presets:
            p_btn = RoundedButton(
                text=label_text,
                font_size="12sp",
                bg_color=COLOR_CARD_LIGHT,
                radius=[6, 6, 6, 6]
            )
            p_btn.bind(on_release=lambda inst, d=days: self._set_preset_date(d))
            quick_dates.add_widget(p_btn)
        date_card.add_widget(quick_dates)

        form_box.add_widget(date_card)

        # Action buttons
        save_btn = RoundedButton(
            text="Create Savings Goal",
            bg_color=COLOR_PRIMARY,
            size_hint_y=None,
            height=48,
            font_size="15sp"
        )
        save_btn.bind(on_release=self._save_goal)
        form_box.add_widget(save_btn)

        cancel_btn = RoundedButton(
            text="Cancel",
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=42,
            font_size="14sp"
        )
        cancel_btn.bind(on_release=self._on_cancel)
        form_box.add_widget(cancel_btn)

        scroll.add_widget(form_box)
        root.add_widget(scroll)

        # Persistent Bottom Navigation Dock
        bottom_nav = BottomNavBar(active_route="savings_goals_screen_5")
        root.add_widget(bottom_nav)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        settings = get_settings()
        curr = settings.get("currency", "$")
        self.target_input.label.text = f"Target Amount ({curr})"
        self.initial_input.label.text = f"Initial Saved Deposit ({curr})"

        # Reset fields to defaults
        self.title_input.text = ""
        self.target_input.text = ""
        self.initial_input.text = "0.00"
        self._set_preset_date(180)
        self._select_category("Emergency")

    def _select_category(self, cat):
        self.selected_category = cat
        for c_name, btn in self.category_buttons.items():
            if c_name == cat:
                btn.set_bg_color(COLOR_PRIMARY)
                btn.color = (1, 1, 1, 1)
            else:
                btn.set_bg_color(COLOR_CARD_LIGHT)
                btn.color = COLOR_TEXT_SECONDARY

    def _set_preset_date(self, days):
        future = datetime.now() + timedelta(days=days)
        self.date_input.text = future.strftime("%Y-%m-%d")

    def _save_goal(self, *args):
        title = self.title_input.text.strip()
        target_str = self.target_input.text.strip()
        initial_str = self.initial_input.text.strip()
        date_str = self.date_input.text.strip()

        if not title:
            show_message("Missing Title", "Please enter a name for your savings goal.")
            return

        try:
            target_amount = float(target_str)
            if target_amount <= 0:
                show_message("Invalid Target", "Target amount must be greater than zero.")
                return
        except (ValueError, TypeError):
            show_message("Invalid Target", "Please enter a valid numeric target amount.")
            return

        initial_amount = 0.0
        if initial_str:
            try:
                initial_amount = float(initial_str)
                if initial_amount < 0:
                    show_message("Invalid Initial Amount", "Initial amount cannot be negative.")
                    return
                if initial_amount > target_amount:
                    show_message("Initial Amount Exceeded", "Initial deposit cannot exceed target amount.")
                    return
            except (ValueError, TypeError):
                show_message("Invalid Initial Amount", "Please enter a valid numeric initial deposit.")
                return

        if not date_str:
            date_str = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            # Basic validation of date structure
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                show_message("Invalid Date", "Please format date as YYYY-MM-DD (e.g. 2025-12-31).")
                return

        new_goal = {
            "title": title,
            "target_amount": target_amount,
            "current_amount": initial_amount,
            "deadline": date_str,
            "icon": self.selected_category
        }

        add_goal(new_goal)

        app = App.get_running_app()
        if app and hasattr(app, "go"):
            app.go("savings_goals_screen_5", direction="right")

    def _on_cancel(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, "go_back"):
            app.go_back()
        elif app and hasattr(app, "go"):
            app.go("savings_goals_screen_5", direction="right")
