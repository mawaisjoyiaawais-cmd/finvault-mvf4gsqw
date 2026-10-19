from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line

from storage import get_transactions, get_settings, format_currency
from ui import (
    Header, Card, RoundedButton, BottomNavBar,
    COLOR_BG, COLOR_CARD, COLOR_CARD_LIGHT,
    COLOR_PRIMARY, COLOR_INCOME, COLOR_EXPENSE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_MUTED, COLOR_ACCENT
)


class PercentageBar(Widget):
    """Custom progress bar with animated visual rounded caps."""
    def __init__(self, ratio=0.0, bar_color=None, **kwargs):
        super(PercentageBar, self).__init__(**kwargs)
        self.ratio = max(0.0, min(1.0, float(ratio)))
        self.bar_color = bar_color if bar_color is not None else COLOR_PRIMARY
        self.size_hint_y = None
        self.height = 10
        self.bind(pos=self._redraw, size=self._redraw)

    def update_ratio(self, ratio, color=None):
        self.ratio = max(0.0, min(1.0, float(ratio)))
        if color is not None:
            self.bar_color = color
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Background track
            Color(0.18, 0.24, 0.33, 0.8)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[5, 5, 5, 5])
            # Foreground progress bar
            filled_w = max(0.0, self.width * self.ratio)
            if filled_w > 0:
                Color(*self.bar_color)
                RoundedRectangle(pos=self.pos, size=(filled_w, self.height), radius=[5, 5, 5, 5])


class RatioComparisonBar(Widget):
    """Visual dual-color bar representing Income vs Expense proportionality."""
    def __init__(self, income_amount=0.0, expense_amount=0.0, **kwargs):
        super(RatioComparisonBar, self).__init__(**kwargs)
        self.income_amount = max(0.0, float(income_amount))
        self.expense_amount = max(0.0, float(expense_amount))
        self.size_hint_y = None
        self.height = 16
        self.bind(pos=self._redraw, size=self._redraw)

    def update_amounts(self, inc, exp):
        self.income_amount = max(0.0, float(inc))
        self.expense_amount = max(0.0, float(exp))
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        total = self.income_amount + self.expense_amount
        with self.canvas.before:
            # Baseline background track
            Color(0.18, 0.24, 0.33, 0.7)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8, 8, 8, 8])
            if total <= 0:
                return
            inc_ratio = self.income_amount / total
            inc_w = self.width * inc_ratio
            exp_w = self.width - inc_w

            if inc_w > 0:
                Color(*COLOR_INCOME)
                r = [8, 0, 0, 8] if exp_w > 0 else [8, 8, 8, 8]
                RoundedRectangle(pos=(self.x, self.y), size=(inc_w, self.height), radius=r)
            if exp_w > 0:
                Color(*COLOR_EXPENSE)
                r = [0, 8, 8, 0] if inc_w > 0 else [8, 8, 8, 8]
                RoundedRectangle(pos=(self.x + inc_w, self.y), size=(exp_w, self.height), radius=r)


class ReportsScreenScreen4(Screen):
    def __init__(self, **kwargs):
        super(ReportsScreenScreen4, self).__init__(**kwargs)
        self.available_months = []
        self.selected_month_idx = 0

        # Root layout
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*COLOR_BG)
            RoundedRectangle(pos=root.pos, size=root.size)

        # Top Header
        header = Header(title="Monthly Analytics", show_back=True)
        root.add_widget(header)

        # Scrollable content area
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[14, 12, 14, 16],
            spacing=12
        )
        self.content_layout.bind(minimum_height=self.content_layout.setter("height"))

        # 1. Month Picker Bar
        self.month_bar = self._build_month_selector()
        self.content_layout.add_widget(self.month_bar)

        # 2. Ratio Card: Income vs Expense
        self.ratio_card = Card(orientation="vertical", size_hint_y=None, height=130, padding=[14, 12, 14, 12], spacing=8)
        self._init_ratio_card()
        self.content_layout.add_widget(self.ratio_card)

        # 3. Monthly Spend Overview Card
        self.overview_card = Card(orientation="vertical", size_hint_y=None, height=84, padding=[14, 10, 14, 10], spacing=4)
        self._init_overview_card()
        self.content_layout.add_widget(self.overview_card)

        # 4. Top Spending Category Highlight
        self.alert_card = Card(
            orientation="horizontal",
            size_hint_y=None,
            height=68,
            padding=[14, 10, 14, 10],
            spacing=10,
            bg_color=(0.18, 0.14, 0.20, 1.0),
            border_color=(0.937, 0.267, 0.267, 0.5)
        )
        self._init_alert_card()
        self.content_layout.add_widget(self.alert_card)

        # Section Title for Breakdown
        sec_title = Label(
            text="Expense Category Breakdown",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=26,
            halign="left",
            valign="middle"
        )
        sec_title.bind(size=sec_title.setter("text_size"))
        self.content_layout.add_widget(sec_title)

        # 5. Dynamic Container for Categorized Items
        self.categories_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.categories_container.bind(minimum_height=self.categories_container.setter("height"))
        self.content_layout.add_widget(self.categories_container)

        self.scroll.add_widget(self.content_layout)
        root.add_widget(self.scroll)

        # Persistent Bottom Navigation
        self.nav_bar = BottomNavBar(active_route="reports_screen_4")
        root.add_widget(self.nav_bar)

        self.add_widget(root)

    def _build_month_selector(self):
        container = Card(orientation="horizontal", size_hint_y=None, height=52, padding=[8, 6, 8, 6], spacing=8)
        
        self.btn_prev_month = RoundedButton(
            text="< Prev",
            size_hint=(None, 1),
            width=70,
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_TEXT_PRIMARY,
            font_size="13sp",
            radius=[8, 8, 8, 8]
        )
        self.btn_prev_month.bind(on_release=self._on_prev_month)
        container.add_widget(self.btn_prev_month)

        self.lbl_month_name = Label(
            text="Current Month",
            font_size="16sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="center",
            valign="middle"
        )
        self.lbl_month_name.bind(size=self.lbl_month_name.setter("text_size"))
        container.add_widget(self.lbl_month_name)

        self.btn_next_month = RoundedButton(
            text="Next >",
            size_hint=(None, 1),
            width=70,
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_TEXT_PRIMARY,
            font_size="13sp",
            radius=[8, 8, 8, 8]
        )
        self.btn_next_month.bind(on_release=self._on_next_month)
        container.add_widget(self.btn_next_month)

        return container

    def _init_ratio_card(self):
        title_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=22)
        lbl = Label(text="Cashflow Balance", font_size="14sp", bold=True, color=COLOR_TEXT_PRIMARY, halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        title_row.add_widget(lbl)
        self.ratio_card.add_widget(title_row)

        self.dual_bar = RatioComparisonBar(income_amount=0, expense_amount=0)
        self.ratio_card.add_widget(self.dual_bar)

        legend_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=36, spacing=10)
        
        # Income summary box
        inc_box = BoxLayout(orientation="vertical", spacing=1)
        inc_header = Label(text="● Total Income", font_size="11sp", color=COLOR_INCOME, halign="left")
        inc_header.bind(size=inc_header.setter("text_size"))
        self.lbl_ratio_inc = Label(text="$0.00", font_size="14sp", bold=True, color=COLOR_TEXT_PRIMARY, halign="left")
        self.lbl_ratio_inc.bind(size=self.lbl_ratio_inc.setter("text_size"))
        inc_box.add_widget(inc_header)
        inc_box.add_widget(self.lbl_ratio_inc)
        legend_row.add_widget(inc_box)

        # Expense summary box
        exp_box = BoxLayout(orientation="vertical", spacing=1)
        exp_header = Label(text="● Total Expense", font_size="11sp", color=COLOR_EXPENSE, halign="right")
        exp_header.bind(size=exp_header.setter("text_size"))
        self.lbl_ratio_exp = Label(text="$0.00", font_size="14sp", bold=True, color=COLOR_TEXT_PRIMARY, halign="right")
        self.lbl_ratio_exp.bind(size=self.lbl_ratio_exp.setter("text_size"))
        exp_box.add_widget(exp_header)
        exp_box.add_widget(self.lbl_ratio_exp)
        legend_row.add_widget(exp_box)

        self.ratio_card.add_widget(legend_row)

    def _init_overview_card(self):
        lbl_h = Label(text="Net Monthly Balance", font_size="12sp", color=COLOR_TEXT_SECONDARY, halign="left")
        lbl_h.bind(size=lbl_h.setter("text_size"))
        self.lbl_net_balance = Label(text="$0.00", font_size="22sp", bold=True, color=COLOR_PRIMARY, halign="left")
        self.lbl_net_balance.bind(size=self.lbl_net_balance.setter("text_size"))
        self.overview_card.add_widget(lbl_h)
        self.overview_card.add_widget(self.lbl_net_balance)

    def _init_alert_card(self):
        icon_lbl = Label(text="!", font_size="22sp", bold=True, color=COLOR_EXPENSE, size_hint=(None, 1), width=28)
        self.alert_card.add_widget(icon_lbl)

        text_box = BoxLayout(orientation="vertical", spacing=2)
        top_h = Label(text="Top Spending Category", font_size="11sp", color=COLOR_TEXT_SECONDARY, halign="left")
        top_h.bind(size=top_h.setter("text_size"))
        self.lbl_top_cat = Label(text="No recorded expenses yet", font_size="13sp", bold=True, color=COLOR_TEXT_PRIMARY, halign="left")
        self.lbl_top_cat.bind(size=self.lbl_top_cat.setter("text_size"))
        text_box.add_widget(top_h)
        text_box.add_widget(self.lbl_top_cat)
        self.alert_card.add_widget(text_box)

    def on_pre_enter(self, *args):
        self._refresh_month_choices()
        self._render_report()

    def _refresh_month_choices(self):
        transactions = get_transactions()
        months_found = set()
        for t in transactions:
            d_str = t.get("date", "")
            if len(d_str) >= 7:
                months_found.add(d_str[:7])
        now_key = datetime.now().strftime("%Y-%m")
        months_found.add(now_key)
        self.available_months = sorted(list(months_found), reverse=True)
        if self.selected_month_idx >= len(self.available_months):
            self.selected_month_idx = 0

    def _get_current_selected_month_key(self):
        if not self.available_months:
            return datetime.now().strftime("%Y-%m")
        return self.available_months[self.selected_month_idx]

    def _on_prev_month(self, instance):
        if self.selected_month_idx < len(self.available_months) - 1:
            self.selected_month_idx += 1
            self._render_report()

    def _on_next_month(self, instance):
        if self.selected_month_idx > 0:
            self.selected_month_idx -= 1
            self._render_report()

    def _render_report(self):
        month_key = self._get_current_selected_month_key()
        try:
            dt = datetime.strptime(month_key, "%Y-%m")
            display_name = dt.strftime("%B %Y")
        except Exception:
            display_name = month_key

        self.lbl_month_name.text = display_name
        self.btn_prev_month.disabled = (self.selected_month_idx >= len(self.available_months) - 1)
        self.btn_next_month.disabled = (self.selected_month_idx <= 0)
        self.btn_prev_month.opacity = 0.4 if self.btn_prev_month.disabled else 1.0
        self.btn_next_month.opacity = 0.4 if self.btn_next_month.disabled else 1.0

        transactions = get_transactions()
        month_txs = [t for t in transactions if str(t.get("date", "")).startswith(month_key)]

        total_income = 0.0
        total_expense = 0.0
        expense_by_cat = {}

        for t in month_txs:
            try:
                amt = float(t.get("amount", 0))
            except (ValueError, TypeError):
                amt = 0.0
            t_type = str(t.get("type", "")).lower()
            if t_type == "income":
                total_income += amt
            else:
                total_expense += amt
                cat = t.get("category") or "Other"
                expense_by_cat[cat] = expense_by_cat.get(cat, 0.0) + amt

        net_val = total_income - total_expense
        settings = get_settings()
        cur = settings.get("currency", "$")

        # Update Summary balances
        self.lbl_ratio_inc.text = format_currency(total_income, cur)
        self.lbl_ratio_exp.text = format_currency(total_expense, cur)
        self.dual_bar.update_amounts(total_income, total_expense)

        if net_val >= 0:
            self.lbl_net_balance.text = f"+{format_currency(net_val, cur)}"
            self.lbl_net_balance.color = COLOR_INCOME
        else:
            self.lbl_net_balance.text = f"-{format_currency(abs(net_val), cur)}"
            self.lbl_net_balance.color = COLOR_EXPENSE

        # Update Highest spending category alert
        if expense_by_cat:
            sorted_cats = sorted(expense_by_cat.items(), key=lambda x: x[1], reverse=True)
            top_cat, top_amt = sorted_cats[0]
            ratio_of_expense = (top_amt / total_expense * 100) if total_expense > 0 else 0
            self.lbl_top_cat.text = f"{top_cat}: {format_currency(top_amt, cur)} ({ratio_of_expense:.1f}% of total)"
        else:
            self.lbl_top_cat.text = "No recorded expenses this month"

        # Render breakdown list
        self.categories_container.clear_widgets()

        if not expense_by_cat:
            empty_card = Card(size_hint_y=None, height=70, padding=[12, 12, 12, 12])
            empty_lbl = Label(
                text="No expense transactions found for this period.",
                color=COLOR_TEXT_SECONDARY,
                font_size="13sp",
                halign="center",
                valign="middle"
            )
            empty_lbl.bind(size=empty_lbl.setter("text_size"))
            empty_card.add_widget(empty_lbl)
            self.categories_container.add_widget(empty_card)
            return

        sorted_items = sorted(expense_by_cat.items(), key=lambda x: x[1], reverse=True)
        color_palette = [
            (0.937, 0.267, 0.267, 1.0),  # Red
            (0.960, 0.620, 0.125, 1.0),  # Orange
            (0.231, 0.510, 0.965, 1.0),  # Blue
            (0.655, 0.384, 0.965, 1.0),  # Purple
            (0.063, 0.725, 0.506, 1.0),  # Teal
            (0.850, 0.350, 0.650, 1.0),  # Pink
            (0.400, 0.800, 0.400, 1.0),  # Mint
        ]

        for idx, (cat_name, cat_amount) in enumerate(sorted_items):
            cat_ratio = (cat_amount / total_expense) if total_expense > 0 else 0
            cat_color = color_palette[idx % len(color_palette)]
            card = self._build_category_card(cat_name, cat_amount, cat_ratio, cat_color, month_key, month_txs)
            self.categories_container.add_widget(card)

    def _build_category_card(self, cat_name, cat_amount, ratio, bar_color, month_key, month_txs):
        card = Card(orientation="vertical", size_hint_y=None, height=84, padding=[12, 10, 12, 10], spacing=6)
        
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=24)
        
        name_lbl = Label(
            text=cat_name,
            font_size="14sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle"
        )
        name_lbl.bind(size=name_lbl.setter("text_size"))
        top_row.add_widget(name_lbl)

        pct_lbl = Label(
            text=f"{ratio * 100:.1f}%",
            font_size="13sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint=(None, 1),
            width=55,
            halign="right",
            valign="middle"
        )
        pct_lbl.bind(size=pct_lbl.setter("text_size"))
        top_row.add_widget(pct_lbl)

        amt_lbl = Label(
            text=format_currency(cat_amount),
            font_size="14sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint=(None, 1),
            width=90,
            halign="right",
            valign="middle"
        )
        amt_lbl.bind(size=amt_lbl.setter("text_size"))
        top_row.add_widget(amt_lbl)
        card.add_widget(top_row)

        # Progress visual percentage bar
        pbar = PercentageBar(ratio=ratio, bar_color=bar_color)
        card.add_widget(pbar)

        # Sub-row with count and interactive tap hint
        sub_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=18)
        related_count = sum(1 for t in month_txs if t.get("category") == cat_name and str(t.get("type", "")).lower() != "income")
        
        count_lbl = Label(
            text=f"{related_count} entries recorded",
            font_size="11sp",
            color=COLOR_MUTED,
            halign="left"
        )
        count_lbl.bind(size=count_lbl.setter("text_size"))
        sub_row.add_widget(count_lbl)

        view_btn = RoundedButton(
            text="View items >",
            size_hint=(None, 1),
            width=85,
            bg_color=(0.18, 0.24, 0.33, 0.7),
            text_color=COLOR_ACCENT,
            font_size="11sp",
            radius=[6, 6, 6, 6]
        )
        view_btn.bind(on_release=lambda inst, c=cat_name, m=month_key: self._show_category_details_modal(c, m))
        sub_row.add_widget(view_btn)
        card.add_widget(sub_row)

        return card

    def _show_category_details_modal(self, category_name, month_key):
        transactions = get_transactions()
        matched = [
            t for t in transactions
            if t.get("category") == category_name
            and str(t.get("date", "")).startswith(month_key)
            and str(t.get("type", "")).lower() != "income"
        ]
        matched.sort(key=lambda x: str(x.get("date", "")), reverse=True)

        content = BoxLayout(orientation="vertical", spacing=10, padding=[12, 12, 12, 12])
        
        # Header count
        top_desc = Label(
            text=f"{len(matched)} transactions under '{category_name}' in {month_key}",
            font_size="12sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="center"
        )
        top_desc.bind(size=top_desc.setter("text_size"))
        content.add_widget(top_desc)

        # Scrollable items
        sv = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=8)
        list_layout.bind(minimum_height=list_layout.setter("height"))

        settings = get_settings()
        cur = settings.get("currency", "$")

        for item in matched:
            row = Card(orientation="horizontal", size_hint_y=None, height=48, padding=[10, 6, 10, 6], bg_color=COLOR_CARD_LIGHT)
            
            info_col = BoxLayout(orientation="vertical", spacing=2)
            note_txt = item.get("note") or item.get("category") or "Expense"
            lbl_note = Label(text=note_txt, font_size="13sp", color=COLOR_TEXT_PRIMARY, halign="left")
            lbl_note.bind(size=lbl_note.setter("text_size"))
            lbl_date = Label(text=item.get("date", ""), font_size="11sp", color=COLOR_MUTED, halign="left")
            lbl_date.bind(size=lbl_date.setter("text_size"))
            info_col.add_widget(lbl_note)
            info_col.add_widget(lbl_date)
            row.add_widget(info_col)

            amt_lbl = Label(
                text=f"-{format_currency(item.get('amount', 0), cur)}",
                font_size="13sp",
                bold=True,
                color=COLOR_EXPENSE,
                size_hint=(None, 1),
                width=85,
                halign="right"
            )
            amt_lbl.bind(size=amt_lbl.setter("text_size"))
            row.add_widget(amt_lbl)
            list_layout.add_widget(row)

        if not matched:
            no_items_lbl = Label(text="No matching records found.", color=COLOR_MUTED, size_hint_y=None, height=40)
            list_layout.add_widget(no_items_lbl)

        sv.add_widget(list_layout)
        content.add_widget(sv)

        popup = Popup(
            title=f"{category_name} Details",
            title_size="16sp",
            title_color=COLOR_TEXT_PRIMARY,
            content=content,
            size_hint=(0.92, 0.65),
            auto_dismiss=False,
            separator_color=COLOR_PRIMARY
        )

        close_btn = RoundedButton(
            text="Close",
            size_hint=(1, None),
            height=42,
            bg_color=COLOR_PRIMARY,
            font_size="14sp"
        )
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
