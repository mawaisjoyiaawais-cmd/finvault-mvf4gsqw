from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

from storage import (
    get_settings,
    save_settings,
    get_transactions,
    get_goals,
    format_currency,
)
from ui import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_INCOME,
    COLOR_EXPENSE,
    COLOR_ACCENT,
    COLOR_MUTED,
    RoundedButton,
    Card,
    BottomNavBar,
    show_message,
)


class ProgressBarWidget(Widget):
    def __init__(self, progress=0.0, bar_color=COLOR_PRIMARY, **kwargs):
        super(ProgressBarWidget, self).__init__(**kwargs)
        self.progress = max(0.0, min(1.0, progress))
        self.bar_color = bar_color
        self.size_hint_y = None
        self.height = 8
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self._update_canvas()

    def _update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.25, 0.35, 1.0)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[4, 4, 4, 4])
            if self.progress > 0:
                Color(*self.bar_color)
                fill_width = max(6.0, self.width * self.progress)
                RoundedRectangle(
                    pos=self.pos,
                    size=(fill_width, self.height),
                    radius=[4, 4, 4, 4],
                )


class DashboardScreenScreen1(Screen):
    def __init__(self, **kwargs):
        super(DashboardScreenScreen1, self).__init__(**kwargs)
        self.privacy_mode = False
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")

        # Top Custom Header
        header_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=60,
            padding=[16, 8, 16, 8],
            spacing=8,
        )
        with header_box.canvas.before:
            Color(0.08, 0.12, 0.20, 1.0)
            self.hdr_rect = RoundedRectangle(pos=header_box.pos, size=header_box.size)
        header_box.bind(
            pos=lambda inst, val: setattr(self.hdr_rect, "pos", val),
            size=lambda inst, val: setattr(self.hdr_rect, "size", val),
        )

        title_col = BoxLayout(orientation="vertical", spacing=2)
        self.app_title_lbl = Label(
            text="FinVault",
            font_size="18sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        self.app_title_lbl.bind(size=self.app_title_lbl.setter("text_size"))

        self.month_lbl = Label(
            text=datetime.now().strftime("%B %Y"),
            font_size="12sp",
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle",
        )
        self.month_lbl.bind(size=self.month_lbl.setter("text_size"))

        title_col.add_widget(self.app_title_lbl)
        title_col.add_widget(self.month_lbl)
        header_box.add_widget(title_col)

        # Privacy Toggle Button
        self.privacy_btn = RoundedButton(
            text="Hide",
            size_hint=(None, 1),
            width=70,
            font_size="13sp",
            bg_color=COLOR_CARD_LIGHT,
        )
        self.privacy_btn.bind(on_release=self._toggle_privacy)
        header_box.add_widget(self.privacy_btn)

        root.add_widget(header_box)

        # Main Scrollable Body
        self.scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.content_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[14, 14, 14, 20],
            spacing=14,
        )
        self.content_layout.bind(
            minimum_height=self.content_layout.setter("height")
        )

        # Balance Card
        self.balance_card = self._create_balance_card()
        self.content_layout.add_widget(self.balance_card)

        # Quick Actions Row
        quick_actions = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=48, spacing=10
        )
        add_tx_btn = RoundedButton(
            text="+ Add Transaction",
            bg_color=COLOR_PRIMARY,
            font_size="14sp",
            bold=True,
        )
        add_tx_btn.bind(on_release=lambda *args: App.get_running_app().go("add_transaction_screen_2"))
        quick_actions.add_widget(add_tx_btn)

        add_goal_btn = RoundedButton(
            text="+ New Goal",
            bg_color=COLOR_ACCENT,
            font_size="14sp",
            bold=True,
            size_hint=(0.48, 1),
        )
        add_goal_btn.bind(on_release=lambda *args: App.get_running_app().go("add_goal_screen_6"))
        quick_actions.add_widget(add_goal_btn)
        self.content_layout.add_widget(quick_actions)

        # Recent Transactions Section Card
        self.recent_tx_card = Card(
            orientation="vertical",
            padding=14,
            spacing=10,
            size_hint_y=None,
        )
        self.recent_tx_card.bind(
            minimum_height=self.recent_tx_card.setter("height")
        )
        self.content_layout.add_widget(self.recent_tx_card)

        # Savings Goals Preview Section Card
        self.goals_card = Card(
            orientation="vertical",
            padding=14,
            spacing=10,
            size_hint_y=None,
        )
        self.goals_card.bind(minimum_height=self.goals_card.setter("height"))
        self.content_layout.add_widget(self.goals_card)

        self.scroll.add_widget(self.content_layout)
        root.add_widget(self.scroll)

        # Persistent Bottom Nav Dock
        self.bottom_nav = BottomNavBar(active_route="dashboard_screen_1")
        root.add_widget(self.bottom_nav)

        self.add_widget(root)

    def _create_balance_card(self):
        card = Card(orientation="vertical", padding=16, spacing=10, size_hint_y=None, height=164)
        
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=20)
        bal_title = Label(
            text="TOTAL NET BALANCE",
            font_size="12sp",
            color=COLOR_TEXT_SECONDARY,
            bold=True,
            halign="left",
            valign="middle",
        )
        bal_title.bind(size=bal_title.setter("text_size"))
        top_row.add_widget(bal_title)
        card.add_widget(top_row)

        self.total_bal_lbl = Label(
            text="$0.00",
            font_size="28sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=40,
            halign="left",
            valign="middle",
        )
        self.total_bal_lbl.bind(size=self.total_bal_lbl.setter("text_size"))
        card.add_widget(self.total_bal_lbl)

        # Income & Expense Sub-Cards Row
        stats_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=62)

        # Income Subcard
        inc_box = BoxLayout(orientation="vertical", padding=[10, 6, 10, 6], spacing=2)
        with inc_box.canvas.before:
            Color(0.08, 0.22, 0.16, 0.9)
            inc_rect = RoundedRectangle(pos=inc_box.pos, size=inc_box.size, radius=[8, 8, 8, 8])
        inc_box.bind(
            pos=lambda inst, val: setattr(inc_rect, "pos", val),
            size=lambda inst, val: setattr(inc_rect, "size", val),
        )
        inc_lbl = Label(text="Income", font_size="11sp", color=COLOR_TEXT_SECONDARY, halign="left", valign="middle")
        inc_lbl.bind(size=inc_lbl.setter("text_size"))
        self.income_val_lbl = Label(
            text="+$0.00", font_size="15sp", bold=True, color=COLOR_INCOME, halign="left", valign="middle"
        )
        self.income_val_lbl.bind(size=self.income_val_lbl.setter("text_size"))
        inc_box.add_widget(inc_lbl)
        inc_box.add_widget(self.income_val_lbl)
        stats_row.add_widget(inc_box)

        # Expense Subcard
        exp_box = BoxLayout(orientation="vertical", padding=[10, 6, 10, 6], spacing=2)
        with exp_box.canvas.before:
            Color(0.24, 0.12, 0.14, 0.9)
            exp_rect = RoundedRectangle(pos=exp_box.pos, size=exp_box.size, radius=[8, 8, 8, 8])
        exp_box.bind(
            pos=lambda inst, val: setattr(exp_rect, "pos", val),
            size=lambda inst, val: setattr(exp_rect, "size", val),
        )
        exp_lbl = Label(text="Expenses", font_size="11sp", color=COLOR_TEXT_SECONDARY, halign="left", valign="middle")
        exp_lbl.bind(size=exp_lbl.setter("text_size"))
        self.expense_val_lbl = Label(
            text="-$0.00", font_size="15sp", bold=True, color=COLOR_EXPENSE, halign="left", valign="middle"
        )
        self.expense_val_lbl.bind(size=self.expense_val_lbl.setter("text_size"))
        exp_box.add_widget(exp_lbl)
        exp_box.add_widget(self.expense_val_lbl)
        stats_row.add_widget(exp_box)

        card.add_widget(stats_row)
        return card

    def _toggle_privacy(self, *args):
        settings = get_settings()
        self.privacy_mode = not self.privacy_mode
        settings["privacy_mode"] = self.privacy_mode
        save_settings(settings)
        self._refresh_values()

    def on_pre_enter(self, *args):
        settings = get_settings()
        self.privacy_mode = settings.get("privacy_mode", False)
        self.month_lbl.text = datetime.now().strftime("%B %Y")
        self._refresh_values()

    def _format_masked(self, amount, currency, prefix=""):
        if self.privacy_mode:
            return f"{prefix}{currency} ••••"
        formatted = format_currency(abs(amount), currency)
        return f"{prefix}{formatted}"

    def _refresh_values(self):
        settings = get_settings()
        currency = settings.get("currency", "$")

        # Update privacy button label
        self.privacy_btn.text = "Show" if self.privacy_mode else "Hide"

        transactions = get_transactions()
        goals = get_goals()

        total_income = 0.0
        total_expense = 0.0

        for t in transactions:
            try:
                amt = float(t.get("amount", 0.0))
            except (ValueError, TypeError):
                amt = 0.0

            tx_type = str(t.get("type", "")).strip().lower()
            if tx_type == "income":
                total_income += amt
            else:
                total_expense += amt

        net_balance = total_income - total_expense

        # Update balance values
        if self.privacy_mode:
            self.total_bal_lbl.text = f"{currency} ••••••"
            self.income_val_lbl.text = f"+{currency} ••••"
            self.expense_val_lbl.text = f"-{currency} ••••"
        else:
            if net_balance < 0:
                self.total_bal_lbl.text = f"-{format_currency(abs(net_balance), currency)}"
                self.total_bal_lbl.color = COLOR_EXPENSE
            else:
                self.total_bal_lbl.text = format_currency(net_balance, currency)
                self.total_bal_lbl.color = COLOR_TEXT_PRIMARY

            self.income_val_lbl.text = f"+{format_currency(total_income, currency)}"
            self.expense_val_lbl.text = f"-{format_currency(total_expense, currency)}"

        # Populate Recent Transactions
        self._render_recent_transactions(transactions, currency)

        # Populate Savings Goals Preview
        self._render_goals_preview(goals, currency)

    def _render_recent_transactions(self, transactions, currency):
        self.recent_tx_card.clear_widgets()

        header_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28)
        sec_title = Label(
            text="Recent Activity",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        sec_title.bind(size=sec_title.setter("text_size"))
        header_row.add_widget(sec_title)

        view_all_btn = RoundedButton(
            text="View All >",
            size_hint=(None, 1),
            width=80,
            font_size="12sp",
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_ACCENT,
        )
        view_all_btn.bind(on_release=lambda *args: App.get_running_app().go("transaction_history_screen_3"))
        header_row.add_widget(view_all_btn)
        self.recent_tx_card.add_widget(header_row)

        recent_items = transactions[:3]
        if not recent_items:
            empty_lbl = Label(
                text="No transactions recorded yet.\nTap '+ Add Transaction' to start.",
                font_size="13sp",
                color=COLOR_MUTED,
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=60,
            )
            empty_lbl.bind(size=empty_lbl.setter("text_size"))
            self.recent_tx_card.add_widget(empty_lbl)
            return

        for tx in recent_items:
            tx_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=52, spacing=10)
            
            # Left Category / Note Column
            info_col = BoxLayout(orientation="vertical", spacing=2)
            cat_name = tx.get("category", "General")
            note_text = tx.get("note", "").strip() or cat_name
            date_text = tx.get("date", "")

            lbl_main = Label(
                text=note_text,
                font_size="14sp",
                bold=True,
                color=COLOR_TEXT_PRIMARY,
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
            lbl_main.bind(size=lbl_main.setter("text_size"))
            lbl_sub = Label(
                text=f"{cat_name} • {date_text}",
                font_size="11sp",
                color=COLOR_TEXT_SECONDARY,
                halign="left",
                valign="middle",
            )
            lbl_sub.bind(size=lbl_sub.setter("text_size"))
            info_col.add_widget(lbl_main)
            info_col.add_widget(lbl_sub)
            tx_row.add_widget(info_col)

            # Right Amount
            is_income = str(tx.get("type", "")).strip().lower() == "income"
            try:
                amt = float(tx.get("amount", 0.0))
            except (ValueError, TypeError):
                amt = 0.0

            sign = "+" if is_income else "-"
            color = COLOR_INCOME if is_income else COLOR_EXPENSE

            if self.privacy_mode:
                amt_display = f"{sign}{currency} ••••"
            else:
                amt_display = f"{sign}{format_currency(amt, currency)}"

            amt_lbl = Label(
                text=amt_display,
                font_size="14sp",
                bold=True,
                color=color,
                size_hint=(None, 1),
                width=110,
                halign="right",
                valign="middle",
            )
            amt_lbl.bind(size=amt_lbl.setter("text_size"))
            tx_row.add_widget(amt_lbl)

            self.recent_tx_card.add_widget(tx_row)

    def _render_goals_preview(self, goals, currency):
        self.goals_card.clear_widgets()

        header_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28)
        sec_title = Label(
            text="Savings Goals Preview",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle",
        )
        sec_title.bind(size=sec_title.setter("text_size"))
        header_row.add_widget(sec_title)

        view_goals_btn = RoundedButton(
            text="Manage >",
            size_hint=(None, 1),
            width=80,
            font_size="12sp",
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_ACCENT,
        )
        view_goals_btn.bind(on_release=lambda *args: App.get_running_app().go("savings_goals_screen_5"))
        header_row.add_widget(view_goals_btn)
        self.goals_card.add_widget(header_row)

        preview_goals = goals[:2]
        if not preview_goals:
            empty_lbl = Label(
                text="No savings goals yet.\nTap '+ New Goal' to begin your target.",
                font_size="13sp",
                color=COLOR_MUTED,
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=60,
            )
            empty_lbl.bind(size=empty_lbl.setter("text_size"))
            self.goals_card.add_widget(empty_lbl)
            return

        for g in preview_goals:
            g_box = BoxLayout(orientation="vertical", size_hint_y=None, height=62, spacing=4)
            
            top_meta = BoxLayout(orientation="horizontal", size_hint_y=None, height=20)
            title_lbl = Label(
                text=g.get("title", "Goal"),
                font_size="13sp",
                bold=True,
                color=COLOR_TEXT_PRIMARY,
                halign="left",
                valign="middle",
            )
            title_lbl.bind(size=title_lbl.setter("text_size"))

            try:
                current_amt = float(g.get("current_amount", 0.0))
                target_amt = float(g.get("target_amount", 1.0))
            except (ValueError, TypeError):
                current_amt = 0.0
                target_amt = 1.0

            ratio = (current_amt / target_amt) if target_amt > 0 else 0.0
            pct_text = f"{int(min(1.0, ratio) * 100)}%"

            if self.privacy_mode:
                val_text = f"•••• / •••• ({pct_text})"
            else:
                val_text = f"{format_currency(current_amt, currency)} / {format_currency(target_amt, currency)} ({pct_text})"

            amt_lbl = Label(
                text=val_text,
                font_size="11sp",
                color=COLOR_TEXT_SECONDARY,
                halign="right",
                valign="middle",
            )
            amt_lbl.bind(size=amt_lbl.setter("text_size"))

            top_meta.add_widget(title_lbl)
            top_meta.add_widget(amt_lbl)
            g_box.add_widget(top_meta)

            prog_bar = ProgressBarWidget(progress=ratio, bar_color=COLOR_PRIMARY)
            g_box.add_widget(prog_bar)
            self.goals_card.add_widget(g_box)
