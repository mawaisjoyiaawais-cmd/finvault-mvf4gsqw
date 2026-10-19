from datetime import datetime, timedelta
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.app import App

from storage import add_transaction, get_settings
from ui import (
    Header,
    RoundedButton,
    Card,
    LabeledInput,
    BottomNavBar,
    show_message,
    COLOR_PRIMARY,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_INCOME,
    COLOR_EXPENSE,
    COLOR_MUTED,
)


EXPENSE_CATEGORIES = [
    "Food", "Transport", "Shopping", "Entertainment",
    "Rent", "Utilities", "Health", "Other"
]

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Investment", "Bonus",
    "Gift", "Other"
]


class AddTransactionScreenScreen2(Screen):
    def __init__(self, **kwargs):
        super(AddTransactionScreenScreen2, self).__init__(**kwargs)
        self.tx_type = "expense"
        self.selected_category = "Food"
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.currency_symbol = "$"
        self.category_buttons = {}

        root = BoxLayout(orientation="vertical", spacing=0)
        root.add_widget(Header(title="Add Transaction", show_back=True))

        scroll = ScrollView(do_scroll_x=False)
        self.form_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=16,
            padding=[16, 14, 16, 20]
        )
        self.form_container.bind(minimum_height=self.form_container.setter("height"))

        # Type Toggle (Expense / Income)
        type_card = Card(size_hint_y=None, height=52, padding=[4, 4, 4, 4])
        self.btn_expense = RoundedButton(
            text="Expense",
            font_size="14sp",
            bg_color=COLOR_EXPENSE,
            radius=[10, 10, 10, 10]
        )
        self.btn_expense.bind(on_release=lambda x: self.set_type("expense"))

        self.btn_income = RoundedButton(
            text="Income",
            font_size="14sp",
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_TEXT_SECONDARY,
            radius=[10, 10, 10, 10]
        )
        self.btn_income.bind(on_release=lambda x: self.set_type("income"))

        type_card.add_widget(self.btn_expense)
        type_card.add_widget(self.btn_income)
        self.form_container.add_widget(type_card)

        # Amount Card
        amount_card = Card(orientation="vertical", size_hint_y=None, height=92, padding=[14, 10, 14, 10], spacing=4)
        lbl_amount = Label(
            text="AMOUNT",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=18,
            halign="left",
            valign="middle"
        )
        lbl_amount.bind(size=lbl_amount.setter("text_size"))
        amount_card.add_widget(lbl_amount)

        input_row = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=48)
        self.currency_label = Label(
            text="$",
            font_size="24sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint=(None, 1),
            width=30
        )
        input_row.add_widget(self.currency_label)

        self.amount_input = TextInput(
            hint_text="0.00",
            input_filter="float",
            multiline=False,
            size_hint=(1, 1),
            background_normal="",
            background_active="",
            background_color=(0.16, 0.22, 0.31, 1.0),
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_MUTED,
            padding=[10, 10, 10, 10],
            font_size="20sp"
        )
        input_row.add_widget(self.amount_input)
        amount_card.add_widget(input_row)
        self.form_container.add_widget(amount_card)

        # Category Section
        cat_label_row = BoxLayout(size_hint_y=None, height=22)
        cat_header = Label(
            text="SELECT CATEGORY",
            font_size="12sp",
            bold=True,
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle"
        )
        cat_header.bind(size=cat_header.setter("text_size"))
        cat_label_row.add_widget(cat_header)
        self.form_container.add_widget(cat_label_row)

        self.category_grid = GridLayout(cols=3, spacing=8, size_hint_y=None)
        self.category_grid.bind(minimum_height=self.category_grid.setter("height"))
        self.form_container.add_widget(self.category_grid)

        # Date Selection Card
        date_card = Card(size_hint_y=None, height=64, padding=[14, 8, 14, 8], orientation="horizontal", spacing=10)
        date_text_box = BoxLayout(orientation="vertical", spacing=2)
        date_lbl_title = Label(
            text="TRANSACTION DATE",
            font_size="11sp",
            bold=True,
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle"
        )
        date_lbl_title.bind(size=date_lbl_title.setter("text_size"))
        date_text_box.add_widget(date_lbl_title)

        self.date_display = Label(
            text=self.selected_date,
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle"
        )
        self.date_display.bind(size=self.date_display.setter("text_size"))
        date_text_box.add_widget(self.date_display)
        date_card.add_widget(date_text_box)

        self.btn_pick_date = RoundedButton(
            text="Change",
            size_hint=(None, None),
            size=(80, 38),
            pos_hint={"center_y": 0.5},
            bg_color=COLOR_CARD_LIGHT,
            font_size="13sp",
            radius=[8, 8, 8, 8]
        )
        self.btn_pick_date.bind(on_release=self.show_date_picker)
        date_card.add_widget(self.btn_pick_date)
        self.form_container.add_widget(date_card)

        # Note Input
        self.note_input = LabeledInput(label_text="NOTE / DESCRIPTION (OPTIONAL)", hint_text="e.g. Dinner, Client payment, Grocery")
        self.form_container.add_widget(self.note_input)

        # Save Button
        self.btn_save = RoundedButton(
            text="Save Transaction",
            size_hint_y=None,
            height=50,
            bg_color=COLOR_PRIMARY,
            font_size="16sp",
            bold=True,
            radius=[12, 12, 12, 12]
        )
        self.btn_save.bind(on_release=self.on_save)
        self.form_container.add_widget(self.btn_save)

        scroll.add_widget(self.form_container)
        root.add_widget(scroll)
        root.add_widget(BottomNavBar(active_route="add_transaction_screen_2"))
        self.add_widget(root)

    def on_pre_enter(self):
        settings = get_settings()
        self.currency_symbol = settings.get("currency", "$")
        self.currency_label.text = self.currency_symbol
        self.amount_input.text = ""
        self.note_input.text = ""
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.date_display.text = self.selected_date
        self.set_type("expense", force_refresh=True)

    def set_type(self, new_type, force_refresh=False):
        if self.tx_type == new_type and not force_refresh:
            return
        self.tx_type = new_type
        if self.tx_type == "expense":
            self.btn_expense.set_bg_color(COLOR_EXPENSE)
            self.btn_expense.color = (1, 1, 1, 1)
            self.btn_income.set_bg_color(COLOR_CARD_LIGHT)
            self.btn_income.color = COLOR_TEXT_SECONDARY
            categories = EXPENSE_CATEGORIES
        else:
            self.btn_income.set_bg_color(COLOR_INCOME)
            self.btn_income.color = (1, 1, 1, 1)
            self.btn_expense.set_bg_color(COLOR_CARD_LIGHT)
            self.btn_expense.color = COLOR_TEXT_SECONDARY
            categories = INCOME_CATEGORIES

        self.selected_category = categories[0]
        self._render_category_chips(categories)

    def _render_category_chips(self, categories):
        self.category_grid.clear_widgets()
        self.category_buttons.clear()
        num_rows = (len(categories) + 2) // 3
        self.category_grid.height = num_rows * 42 + (num_rows - 1) * 8

        for cat in categories:
            is_active = (cat == self.selected_category)
            active_color = COLOR_EXPENSE if self.tx_type == "expense" else COLOR_INCOME
            btn = RoundedButton(
                text=cat,
                font_size="13sp",
                size_hint_y=None,
                height=40,
                bg_color=active_color if is_active else COLOR_CARD,
                text_color=(1, 1, 1, 1) if is_active else COLOR_TEXT_SECONDARY,
                radius=[8, 8, 8, 8]
            )
            btn.bind(on_release=lambda instance, c=cat: self.on_category_selected(c))
            self.category_buttons[cat] = btn
            self.category_grid.add_widget(btn)

    def on_category_selected(self, cat):
        self.selected_category = cat
        active_color = COLOR_EXPENSE if self.tx_type == "expense" else COLOR_INCOME
        for name, btn in self.category_buttons.items():
            if name == cat:
                btn.set_bg_color(active_color)
                btn.color = (1, 1, 1, 1)
            else:
                btn.set_bg_color(COLOR_CARD)
                btn.color = COLOR_TEXT_SECONDARY

    def show_date_picker(self, *args):
        content = BoxLayout(orientation="vertical", spacing=10, padding=12)
        lbl = Label(
            text="Select Date",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=26
        )
        content.add_widget(lbl)

        preset_box = BoxLayout(spacing=6, size_hint_y=None, height=38)
        btn_today = RoundedButton(text="Today", font_size="12sp", bg_color=COLOR_CARD_LIGHT)
        btn_yesterday = RoundedButton(text="Yesterday", font_size="12sp", bg_color=COLOR_CARD_LIGHT)
        preset_box.add_widget(btn_today)
        preset_box.add_widget(btn_yesterday)
        content.add_widget(preset_box)

        custom_input = TextInput(
            text=self.selected_date,
            multiline=False,
            size_hint_y=None,
            height=40,
            background_normal="",
            background_active="",
            background_color=(0.14, 0.18, 0.26, 1.0),
            foreground_color=COLOR_TEXT_PRIMARY,
            padding=[8, 8, 8, 8],
            font_size="14sp"
        )
        content.add_widget(custom_input)

        popup = Popup(
            title="Pick Date (YYYY-MM-DD)",
            title_size="15sp",
            title_color=COLOR_TEXT_PRIMARY,
            content=content,
            size_hint=(0.85, 0.36),
            auto_dismiss=False,
            separator_color=COLOR_PRIMARY
        )

        def set_preset(date_str):
            custom_input.text = date_str

        btn_today.bind(on_release=lambda x: set_preset(datetime.now().strftime("%Y-%m-%d")))
        btn_yesterday.bind(on_release=lambda x: set_preset((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")))

        btn_row = BoxLayout(spacing=8, size_hint_y=None, height=40)
        btn_cancel = RoundedButton(text="Cancel", bg_color=COLOR_CARD_LIGHT)
        btn_cancel.bind(on_release=lambda x: popup.dismiss())

        def apply_date(x):
            entered = custom_input.text.strip()
            try:
                datetime.strptime(entered, "%Y-%m-%d")
                self.selected_date = entered
                self.date_display.text = self.selected_date
                popup.dismiss()
            except ValueError:
                show_message("Invalid Date", "Please format the date as YYYY-MM-DD.")

        btn_ok = RoundedButton(text="Apply", bg_color=COLOR_PRIMARY)
        btn_ok.bind(on_release=apply_date)

        btn_row.add_widget(btn_cancel)
        btn_row.add_widget(btn_ok)
        content.add_widget(btn_row)
        popup.open()

    def on_save(self, *args):
        raw_amount = self.amount_input.text.strip()
        if not raw_amount:
            show_message("Amount Required", "Please enter a valid transaction amount.")
            return
        try:
            amt = float(raw_amount)
            if amt <= 0:
                raise ValueError
        except ValueError:
            show_message("Invalid Amount", "Please enter a positive numeric value.")
            return

        item = {
            "type": self.tx_type,
            "amount": round(amt, 2),
            "category": self.selected_category,
            "date": self.selected_date,
            "note": self.note_input.text.strip()
        }

        add_transaction(item)
        app = App.get_running_app()
        if app and hasattr(app, "go"):
            app.go("dashboard_screen_1", direction="right")
