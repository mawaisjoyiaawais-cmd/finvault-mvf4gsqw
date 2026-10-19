from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.app import App

from storage import get_transactions, delete_transaction, format_currency, get_settings
from ui import (
    Header,
    BottomNavBar,
    RoundedButton,
    Card,
    show_confirm,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_INCOME,
    COLOR_EXPENSE,
    COLOR_MUTED,
)

CATEGORIES = [
    "All",
    "Food",
    "Salary",
    "Rent",
    "Utilities",
    "Transport",
    "Shopping",
    "Entertainment",
    "Health",
    "Other",
]


class TransactionHistoryScreenScreen3(Screen):
    def __init__(self, **kwargs):
        super(TransactionHistoryScreenScreen3, self).__init__(**kwargs)
        self.active_type_filter = "ALL"  # "ALL", "INCOME", "EXPENSE"
        self.active_category_filter = "All"
        self.search_query = ""
        self.currency_symbol = "$"

        with self.canvas.before:
            Color(*COLOR_BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.main_layout = BoxLayout(orientation="vertical", spacing=0)
        self.add_widget(self.main_layout)

        self._build_header()
        self._build_controls()
        self._build_summary_bar()
        self._build_transaction_list()

        self.nav_bar = BottomNavBar(active_route="transaction_history_screen_3")
        self.main_layout.add_widget(self.nav_bar)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _build_header(self):
        add_btn = RoundedButton(
            text="+ Add",
            size_hint=(None, 1),
            width=70,
            bg_color=COLOR_PRIMARY,
            font_size="13sp",
        )
        add_btn.bind(on_release=lambda *args: App.get_running_app().go("add_transaction_screen_2"))
        self.header = Header(title="Transaction History", show_back=True, right_widget=add_btn)
        self.main_layout.add_widget(self.header)

    def _build_controls(self):
        controls_box = BoxLayout(orientation="vertical", size_hint_y=None, height=138, padding=[12, 6, 12, 4], spacing=6)

        # Search bar
        search_card = Card(bg_color=COLOR_CARD, radius=[10, 10, 10, 10], size_hint_y=None, height=40, padding=[10, 2, 10, 2])
        self.search_input = TextInput(
            hint_text="Search note or category...",
            multiline=False,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_MUTED,
            font_size="13sp",
            padding=[0, 8, 0, 8],
        )
        self.search_input.bind(text=self._on_search_change)
        search_card.add_widget(self.search_input)
        controls_box.add_widget(search_card)

        # Type filter chips (All, Income, Expense)
        type_row = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=36)
        self.type_buttons = {}
        for t_type, display in [("ALL", "All"), ("INCOME", "Income"), ("EXPENSE", "Expense")]:
            is_active = (t_type == self.active_type_filter)
            btn = RoundedButton(
                text=display,
                font_size="12sp",
                bg_color=COLOR_PRIMARY if is_active else COLOR_CARD_LIGHT,
                text_color=(1, 1, 1, 1) if is_active else COLOR_TEXT_SECONDARY,
                radius=[8, 8, 8, 8],
            )
            btn.bind(on_release=lambda inst, t=t_type: self._set_type_filter(t))
            self.type_buttons[t_type] = btn
            type_row.add_widget(btn)
        controls_box.add_widget(type_row)

        # Category filter scroll
        cat_scroll = ScrollView(size_hint_y=None, height=38, do_scroll_y=False, do_scroll_x=True)
        self.cat_layout = BoxLayout(orientation="horizontal", spacing=6, size_hint_x=None, height=34)
        self.cat_layout.bind(minimum_width=self.cat_layout.setter("width"))
        self.category_buttons = {}

        for cat in CATEGORIES:
            is_active = (cat == self.active_category_filter)
            c_btn = RoundedButton(
                text=cat,
                font_size="11sp",
                size_hint=(None, None),
                size=(82, 32),
                bg_color=COLOR_PRIMARY if is_active else (0.16, 0.22, 0.31, 1.0),
                text_color=(1, 1, 1, 1) if is_active else COLOR_TEXT_SECONDARY,
                radius=[14, 14, 14, 14],
            )
            c_btn.bind(on_release=lambda inst, c=cat: self._set_category_filter(c))
            self.category_buttons[cat] = c_btn
            self.cat_layout.add_widget(c_btn)

        cat_scroll.add_widget(self.cat_layout)
        controls_box.add_widget(cat_scroll)
        self.main_layout.add_widget(controls_box)

    def _build_summary_bar(self):
        self.summary_card = Card(
            bg_color=(0.10, 0.14, 0.21, 0.95),
            radius=[8, 8, 8, 8],
            size_hint_y=None,
            height=32,
            padding=[14, 0, 14, 0],
        )
        self.summary_left_lbl = Label(
            text="Showing 0 transactions",
            font_size="11sp",
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle",
            size_hint_x=0.6,
        )
        self.summary_left_lbl.bind(size=self.summary_left_lbl.setter("text_size"))

        self.summary_right_lbl = Label(
            text="Net: $0.00",
            font_size="11sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="right",
            valign="middle",
            size_hint_x=0.4,
        )
        self.summary_right_lbl.bind(size=self.summary_right_lbl.setter("text_size"))

        self.summary_card.add_widget(self.summary_left_lbl)
        self.summary_card.add_widget(self.summary_right_lbl)
        self.main_layout.add_widget(self.summary_card)

    def _build_transaction_list(self):
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.list_layout = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=[12, 8, 12, 12])
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        self.main_layout.add_widget(self.scroll)

    def on_pre_enter(self, *args):
        settings = get_settings()
        self.currency_symbol = settings.get("currency", "$")
        self.refresh_list()

    def _on_search_change(self, instance, value):
        self.search_query = value.strip().lower()
        self.refresh_list()

    def _set_type_filter(self, t_type):
        self.active_type_filter = t_type
        for k, btn in self.type_buttons.items():
            if k == t_type:
                btn.set_bg_color(COLOR_PRIMARY)
                btn.color = (1, 1, 1, 1)
            else:
                btn.set_bg_color(COLOR_CARD_LIGHT)
                btn.color = COLOR_TEXT_SECONDARY
        self.refresh_list()

    def _set_category_filter(self, category):
        self.active_category_filter = category
        for c, btn in self.category_buttons.items():
            if c == category:
                btn.set_bg_color(COLOR_PRIMARY)
                btn.color = (1, 1, 1, 1)
            else:
                btn.set_bg_color((0.16, 0.22, 0.31, 1.0))
                btn.color = COLOR_TEXT_SECONDARY
        self.refresh_list()

    def refresh_list(self):
        self.list_layout.clear_widgets()
        raw_txs = get_transactions()

        filtered = []
        total_net = 0.0

        for tx in raw_txs:
            tx_type = str(tx.get("type", "")).upper()
            tx_cat = str(tx.get("category", ""))
            tx_note = str(tx.get("note", ""))
            try:
                tx_amount = float(tx.get("amount", 0.0))
            except (ValueError, TypeError):
                tx_amount = 0.0

            # Apply Type filter
            if self.active_type_filter != "ALL":
                if tx_type != self.active_type_filter:
                    continue

            # Apply Category filter
            if self.active_category_filter != "All":
                if tx_cat.lower() != self.active_category_filter.lower():
                    continue

            # Apply Search filter (matches note or category)
            if self.search_query:
                combined_text = f"{tx_cat} {tx_note}".lower()
                if self.search_query not in combined_text:
                    continue

            filtered.append(tx)
            if tx_type == "INCOME":
                total_net += tx_amount
            else:
                total_net -= tx_amount

        # Update Summary text
        count = len(filtered)
        self.summary_left_lbl.text = f"Showing {count} {'transaction' if count == 1 else 'transactions'}"
        net_prefix = "+" if total_net > 0 else ""
        self.summary_right_lbl.text = f"Net: {net_prefix}{format_currency(total_net, self.currency_symbol)}"
        if total_net > 0:
            self.summary_right_lbl.color = COLOR_INCOME
        elif total_net < 0:
            self.summary_right_lbl.color = COLOR_EXPENSE
        else:
            self.summary_right_lbl.color = COLOR_TEXT_PRIMARY

        if not filtered:
            empty_card = Card(
                bg_color=COLOR_CARD,
                radius=[12, 12, 12, 12],
                size_hint_y=None,
                height=160,
                padding=[20, 20, 20, 20],
            )
            box = BoxLayout(orientation="vertical", spacing=10)
            lbl1 = Label(
                text="No transactions found",
                font_size="15sp",
                bold=True,
                color=COLOR_TEXT_PRIMARY,
                halign="center",
            )
            lbl2 = Label(
                text="Try adjusting filters or record a new transaction.",
                font_size="12sp",
                color=COLOR_TEXT_SECONDARY,
                halign="center",
            )
            lbl1.bind(size=lbl1.setter("text_size"))
            lbl2.bind(size=lbl2.setter("text_size"))
            box.add_widget(lbl1)
            box.add_widget(lbl2)

            add_new_btn = RoundedButton(
                text="+ Add Transaction",
                size_hint=(None, None),
                size=(180, 38),
                pos_hint={"center_x": 0.5},
                bg_color=COLOR_PRIMARY,
                font_size="13sp",
            )
            add_new_btn.bind(on_release=lambda *args: App.get_running_app().go("add_transaction_screen_2"))
            box.add_widget(add_new_btn)

            empty_card.add_widget(box)
            self.list_layout.add_widget(empty_card)
            return

        for item in filtered:
            card = self._create_transaction_card(item)
            self.list_layout.add_widget(card)

    def _create_transaction_card(self, tx):
        is_income = str(tx.get("type", "")).upper() == "INCOME"
        try:
            amt_num = float(tx.get("amount", 0.0))
        except (ValueError, TypeError):
            amt_num = 0.0

        card = Card(
            bg_color=COLOR_CARD,
            radius=[12, 12, 12, 12],
            size_hint_y=None,
            height=72,
            padding=[12, 8, 12, 8],
        )

        row = BoxLayout(orientation="horizontal", spacing=10)

        # Left indicator pill
        pill = BoxLayout(size_hint=(None, None), size=(6, 48), pos_hint={"center_y": 0.5})
        with pill.canvas.before:
            Color(*(COLOR_INCOME if is_income else COLOR_EXPENSE))
            RoundedRectangle(pos=pill.pos, size=pill.size, radius=[3, 3, 3, 3])
        pill.bind(pos=lambda inst, *_: self._sync_pill(inst, is_income), size=lambda inst, *_: self._sync_pill(inst, is_income))
        row.add_widget(pill)

        # Mid section: Category & Note + Date
        mid_box = BoxLayout(orientation="vertical", spacing=3, size_hint_x=0.55)
        category_text = tx.get("category", "General")
        note_text = tx.get("note", "").strip()
        primary_text = note_text if note_text else category_text
        secondary_text = f"{category_text} - {tx.get('date', '')}" if note_text else tx.get("date", "")

        title_lbl = Label(
            text=primary_text,
            font_size="14sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))

        sub_lbl = Label(
            text=secondary_text,
            font_size="11sp",
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        sub_lbl.bind(size=sub_lbl.setter("text_size"))

        mid_box.add_widget(title_lbl)
        mid_box.add_widget(sub_lbl)
        row.add_widget(mid_box)

        # Right section: Amount & Delete Button
        right_box = BoxLayout(orientation="horizontal", spacing=6, size_hint_x=0.45)

        sign = "+" if is_income else "-"
        amount_str = f"{sign}{format_currency(amt_num, self.currency_symbol)}"
        amt_lbl = Label(
            text=amount_str,
            font_size="13sp",
            bold=True,
            color=COLOR_INCOME if is_income else COLOR_EXPENSE,
            halign="right",
            valign="middle",
            size_hint_x=0.68,
        )
        amt_lbl.bind(size=amt_lbl.setter("text_size"))
        right_box.add_widget(amt_lbl)

        del_btn = RoundedButton(
            text="Del",
            size_hint=(None, None),
            size=(42, 34),
            pos_hint={"center_y": 0.5},
            bg_color=(0.32, 0.16, 0.18, 0.85),
            text_color=(0.96, 0.45, 0.45, 1.0),
            font_size="11sp",
            radius=[8, 8, 8, 8],
        )
        del_btn.bind(on_release=lambda *args, t=tx: self._confirm_delete(t))
        right_box.add_widget(del_btn)

        row.add_widget(right_box)
        card.add_widget(row)
        return card

    def _sync_pill(self, pill, is_income):
        pill.canvas.before.clear()
        with pill.canvas.before:
            Color(*(COLOR_INCOME if is_income else COLOR_EXPENSE))
            RoundedRectangle(pos=pill.pos, size=pill.size, radius=[3, 3, 3, 3])

    def _confirm_delete(self, tx):
        tx_id = tx.get("id")
        cat = tx.get("category", "item")
        try:
            amt = float(tx.get("amount", 0))
        except (ValueError, TypeError):
            amt = 0.0
        amt_str = format_currency(amt, self.currency_symbol)

        show_confirm(
            title="Delete Transaction",
            text=f"Permanently delete {cat} transaction of {amt_str}?",
            on_confirm=lambda: self._execute_delete(tx_id),
        )

    def _execute_delete(self, tx_id):
        if tx_id:
            delete_transaction(tx_id)
            self.refresh_list()
