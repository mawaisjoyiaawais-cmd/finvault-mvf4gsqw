from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App

from storage import (
    get_goals,
    update_goal,
    delete_goal,
    format_currency,
    get_settings
)
from ui import (
    Header,
    BottomNavBar,
    Card,
    RoundedButton,
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_EXPENSE,
    COLOR_ACCENT,
    COLOR_MUTED,
    show_confirm,
    show_message
)


class ProgressBarWidget(Widget):
    def __init__(self, progress=0.0, **kwargs):
        super(ProgressBarWidget, self).__init__(**kwargs)
        self.size_hint_y = None
        self.height = 10
        self._progress = max(0.0, min(1.0, float(progress)))
        self.bind(pos=self._redraw, size=self._redraw)

    def set_progress(self, progress):
        self._progress = max(0.0, min(1.0, float(progress)))
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Background track
            Color(0.20, 0.25, 0.35, 0.8)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[5, 5, 5, 5])
            # Fill track
            if self._progress > 0:
                fill_width = max(8.0, self.width * self._progress)
                if self._progress >= 1.0:
                    Color(*COLOR_PRIMARY)
                else:
                    Color(*COLOR_ACCENT)
                RoundedRectangle(pos=self.pos, size=(fill_width, self.height), radius=[5, 5, 5, 5])


class SavingsGoalsScreenScreen5(Screen):
    def __init__(self, **kwargs):
        super(SavingsGoalsScreenScreen5, self).__init__(**kwargs)
        self.currency = "$"
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        # Header with Add Goal shortcut
        add_shortcut_btn = RoundedButton(
            text="+ New",
            bg_color=COLOR_PRIMARY,
            size_hint=(None, 1),
            width=70,
            font_size="13sp"
        )
        add_shortcut_btn.bind(on_release=lambda inst: self._go_add_goal())

        self.header = Header(
            title="Savings Goals",
            show_back=False,
            right_widget=add_shortcut_btn
        )
        root.add_widget(self.header)

        # Main Scrollable Body
        self.scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        self.container = GridLayout(cols=1, spacing=14, size_hint_y=None, padding=[14, 14, 14, 20])
        self.container.bind(minimum_height=self.container.setter("height"))
        self.scroll.add_widget(self.container)
        root.add_widget(self.scroll)

        # Persistent Bottom Navigation
        self.bottom_nav = BottomNavBar(active_route="savings_goals_screen_5")
        root.add_widget(self.bottom_nav)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        settings = get_settings()
        self.currency = settings.get("currency", "$")
        self.refresh_goals()

    def _go_add_goal(self):
        app = App.get_running_app()
        if app and hasattr(app, "go"):
            app.go("add_goal_screen_6")

    def refresh_goals(self):
        self.container.clear_widgets()
        goals = get_goals()

        total_target = sum(float(g.get("target_amount", 0.0)) for g in goals)
        total_saved = sum(float(g.get("current_amount", 0.0)) for g in goals)
        overall_pct = (total_saved / total_target * 100.0) if total_target > 0 else 0.0

        # Overview Banner Card
        overview_card = Card(
            orientation="vertical",
            padding=[16, 14, 16, 14],
            spacing=8,
            size_hint_y=None,
            height=125,
            bg_color=(0.14, 0.20, 0.30, 1.0)
        )

        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=22)
        lbl_title = Label(
            text="TOTAL SAVED ACROSS GOALS",
            font_size="11sp",
            color=COLOR_TEXT_SECONDARY,
            bold=True,
            halign="left",
            valign="middle"
        )
        lbl_title.bind(size=lbl_title.setter("text_size"))
        top_row.add_widget(lbl_title)

        pct_badge = Label(
            text=f"{overall_pct:.1f}% reached",
            font_size="12sp",
            color=COLOR_PRIMARY,
            bold=True,
            halign="right",
            valign="middle",
            size_hint_x=None,
            width=110
        )
        pct_badge.bind(size=pct_badge.setter("text_size"))
        top_row.add_widget(pct_badge)
        overview_card.add_widget(top_row)

        total_amount_lbl = Label(
            text=format_currency(total_saved, self.currency),
            font_size="26sp",
            bold=True,
            color=COLOR_PRIMARY,
            size_hint_y=None,
            height=34,
            halign="left",
            valign="middle"
        )
        total_amount_lbl.bind(size=total_amount_lbl.setter("text_size"))
        overview_card.add_widget(total_amount_lbl)

        prog_bar = ProgressBarWidget(progress=min(1.0, overall_pct / 100.0))
        overview_card.add_widget(prog_bar)

        meta_lbl = Label(
            text=f"Target: {format_currency(total_target, self.currency)}  *  {len(goals)} active target(s)",
            font_size="11sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=18,
            halign="left",
            valign="middle"
        )
        meta_lbl.bind(size=meta_lbl.setter("text_size"))
        overview_card.add_widget(meta_lbl)

        self.container.add_widget(overview_card)

        if not goals:
            # Empty placeholder state card
            empty_card = Card(
                orientation="vertical",
                padding=[20, 30, 20, 30],
                spacing=12,
                size_hint_y=None,
                height=180,
                bg_color=COLOR_CARD
            )
            msg_lbl = Label(
                text="No savings goals established yet!",
                font_size="16sp",
                bold=True,
                color=COLOR_TEXT_PRIMARY,
                halign="center"
            )
            sub_lbl = Label(
                text="Set targets for emergency funds, vacations, or major purchases to monitor your financial milestones.",
                font_size="13sp",
                color=COLOR_TEXT_SECONDARY,
                halign="center"
            )
            msg_lbl.bind(size=msg_lbl.setter("text_size"))
            sub_lbl.bind(size=sub_lbl.setter("text_size"))
            empty_card.add_widget(msg_lbl)
            empty_card.add_widget(sub_lbl)

            create_btn = RoundedButton(
                text="+ Create First Goal",
                bg_color=COLOR_PRIMARY,
                size_hint=(None, None),
                width=190,
                height=42,
                pos_hint={"center_x": 0.5}
            )
            create_btn.bind(on_release=lambda inst: self._go_add_goal())
            empty_card.add_widget(create_btn)
            self.container.add_widget(empty_card)
            return

        # Active Goals List
        for goal in goals:
            card = self._build_goal_card(goal)
            self.container.add_widget(card)

    def _build_goal_card(self, goal):
        goal_id = goal.get("id", "")
        title = goal.get("title", "Savings Goal")
        icon = goal.get("icon", "$")
        target = float(goal.get("target_amount", 0.0))
        current = float(goal.get("current_amount", 0.0))
        deadline = goal.get("deadline", "No deadline")

        pct = (current / target * 100.0) if target > 0 else 0.0
        is_completed = current >= target and target > 0

        card = Card(
            orientation="vertical",
            padding=[14, 12, 14, 12],
            spacing=8,
            size_hint_y=None,
            height=162,
            bg_color=COLOR_CARD,
            border_color=(0.18, 0.45, 0.35, 0.8) if is_completed else None
        )

        # Top Row: Icon + Title + Deadline badge + Delete
        top_bar = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=28)

        icon_label = Label(
            text=f"[{icon}]",
            font_size="14sp",
            bold=True,
            color=COLOR_ACCENT,
            size_hint=(None, 1),
            width=32
        )
        top_bar.add_widget(icon_label)

        title_label = Label(
            text=title,
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle"
        )
        title_label.bind(size=title_label.setter("text_size"))
        top_bar.add_widget(title_label)

        del_btn = RoundedButton(
            text="X",
            font_size="12sp",
            bg_color=(0.35, 0.15, 0.15, 0.7),
            text_color=(0.95, 0.7, 0.7, 1.0),
            size_hint=(None, 1),
            width=28,
            radius=[6, 6, 6, 6]
        )
        del_btn.bind(on_release=lambda inst, gid=goal_id, gtitle=title: self._confirm_delete(gid, gtitle))
        top_bar.add_widget(del_btn)
        card.add_widget(top_bar)

        # Numbers row: Current vs Target
        amount_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=24)
        current_text = format_currency(current, self.currency)
        target_text = format_currency(target, self.currency)
        balance_lbl = Label(
            text=f"{current_text} / {target_text}",
            font_size="14sp",
            bold=True,
            color=COLOR_PRIMARY if is_completed else COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle"
        )
        balance_lbl.bind(size=balance_lbl.setter("text_size"))
        amount_row.add_widget(balance_lbl)

        pct_lbl = Label(
            text=f"{pct:.1f}%" if not is_completed else "COMPLETED",
            font_size="12sp",
            bold=True,
            color=COLOR_PRIMARY if is_completed else COLOR_ACCENT,
            halign="right",
            valign="middle",
            size_hint_x=None,
            width=90
        )
        pct_lbl.bind(size=pct_lbl.setter("text_size"))
        amount_row.add_widget(pct_lbl)
        card.add_widget(amount_row)

        # Progress bar
        ratio = min(1.0, current / target) if target > 0 else 0.0
        pbar = ProgressBarWidget(progress=ratio)
        card.add_widget(pbar)

        # Bottom Row: Deadline & Action Buttons
        bottom_row = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=36)

        target_date_lbl = Label(
            text=f"Due: {deadline}" if deadline else "Ongoing",
            font_size="11sp",
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle"
        )
        target_date_lbl.bind(size=target_date_lbl.setter("text_size"))
        bottom_row.add_widget(target_date_lbl)

        deposit_btn = RoundedButton(
            text="+ Deposit",
            font_size="12sp",
            bg_color=COLOR_PRIMARY,
            size_hint=(None, 1),
            width=85,
            radius=[8, 8, 8, 8]
        )
        deposit_btn.bind(on_release=lambda inst, g=goal: self._prompt_adjust_funds(g, "deposit"))
        bottom_row.add_widget(deposit_btn)

        withdraw_btn = RoundedButton(
            text="- Withdraw",
            font_size="12sp",
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_TEXT_PRIMARY,
            size_hint=(None, 1),
            width=85,
            radius=[8, 8, 8, 8]
        )
        withdraw_btn.bind(on_release=lambda inst, g=goal: self._prompt_adjust_funds(g, "withdraw"))
        bottom_row.add_widget(withdraw_btn)

        card.add_widget(bottom_row)
        return card

    def _prompt_adjust_funds(self, goal, mode):
        action_name = "Deposit Funds" if mode == "deposit" else "Withdraw Funds"
        content = BoxLayout(orientation="vertical", spacing=12, padding=16)

        info_text = f"{action_name} for '{goal.get('title', '')}'"
        lbl_info = Label(
            text=info_text,
            font_size="14sp",
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=26,
            halign="center"
        )
        lbl_info.bind(size=lbl_info.setter("text_size"))
        content.add_widget(lbl_info)

        amount_input = TextInput(
            hint_text=f"Amount ({self.currency})",
            input_filter="float",
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
        content.add_widget(amount_input)

        btn_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=44)
        popup = Popup(
            title=action_name,
            title_size="16sp",
            title_color=COLOR_TEXT_PRIMARY,
            content=content,
            size_hint=(0.86, 0.38),
            auto_dismiss=False,
            separator_color=COLOR_PRIMARY if mode == "deposit" else COLOR_EXPENSE
        )

        def _cancel(inst):
            popup.dismiss()

        def _submit(inst):
            val_str = amount_input.text.strip()
            try:
                delta = float(val_str)
            except ValueError:
                show_message("Invalid Value", "Please enter a valid numeric amount.")
                return

            if delta <= 0:
                show_message("Invalid Value", "Amount must be greater than zero.")
                return

            current = float(goal.get("current_amount", 0.0))
            if mode == "deposit":
                new_val = current + delta
            else:
                if delta > current:
                    show_message("Limit Exceeded", f"Cannot withdraw more than current balance ({format_currency(current, self.currency)}).")
                    return
                new_val = current - delta

            update_goal(goal.get("id"), new_val)
            popup.dismiss()
            self.refresh_goals()

        cancel_btn = RoundedButton(text="Cancel", bg_color=COLOR_CARD_LIGHT)
        cancel_btn.bind(on_release=_cancel)
        btn_row.add_widget(cancel_btn)

        confirm_btn = RoundedButton(
            text="Apply",
            bg_color=COLOR_PRIMARY if mode == "deposit" else COLOR_EXPENSE
        )
        confirm_btn.bind(on_release=_submit)
        btn_row.add_widget(confirm_btn)

        content.add_widget(btn_row)
        popup.open()

    def _confirm_delete(self, goal_id, goal_title):
        def on_confirmed():
            delete_goal(goal_id)
            self.refresh_goals()

        show_confirm(
            "Delete Goal",
            f"Are you sure you want to delete the goal '{goal_title}'?",
            on_confirm=on_confirmed
        )
