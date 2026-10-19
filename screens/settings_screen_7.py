from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App

from storage import (
    get_settings,
    save_settings,
    set_new_pin,
    verify_pin,
    reset_all_data,
    get_transactions,
    get_goals
)
from ui import (
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_BG,
    COLOR_CARD,
    COLOR_CARD_LIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_EXPENSE,
    COLOR_ACCENT,
    COLOR_MUTED,
    RoundedButton,
    Card,
    Header,
    BottomNavBar,
    show_message,
    show_confirm
)


class SettingsScreenScreen7(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreenScreen7, self).__init__(**kwargs)
        self.currency_buttons = {}

        # Root layout
        root = BoxLayout(orientation="vertical", spacing=0)
        with root.canvas.before:
            Color(*COLOR_BG)
            self.bg_rect = RoundedRectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        # Header
        root.add_widget(Header(title="Settings", show_back=False))

        # Scrollable container
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[16, 16, 16, 24],
            spacing=16
        )
        self.content.bind(minimum_height=self.content.setter("height"))

        # 1. Security Card
        self.content.add_widget(self._build_security_card())

        # 2. Currency Card
        self.content.add_widget(self._build_currency_card())

        # 3. Privacy & Display Card
        self.content.add_widget(self._build_preferences_card())

        # 4. Storage & Diagnostics Card
        self.content.add_widget(self._build_data_info_card())

        # 5. Danger Zone Card
        self.content.add_widget(self._build_danger_card())

        scroll.add_widget(self.content)
        root.add_widget(scroll)

        # Bottom Navigation Dock
        root.add_widget(BottomNavBar(active_route="settings_screen_7"))

        self.add_widget(root)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    # ========================== UI SECTIONS ==========================

    def _build_security_card(self):
        card = Card(orientation="vertical", padding=[16, 14, 16, 14], spacing=10, size_hint_y=None, height=164)
        
        title = Label(
            text="Security & Authentication",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=24,
            halign="left",
            valign="middle"
        )
        title.bind(size=title.setter("text_size"))
        card.add_widget(title)

        desc = Label(
            text="Offline 4-digit PIN secures your financial ledger.",
            font_size="12sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        desc.bind(size=desc.setter("text_size"))
        card.add_widget(desc)

        btn_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=44)
        
        change_pin_btn = RoundedButton(
            text="Change 4-Digit PIN",
            bg_color=COLOR_CARD_LIGHT,
            text_color=COLOR_TEXT_PRIMARY,
            font_size="13sp"
        )
        change_pin_btn.bind(on_release=lambda x: self._open_change_pin_dialog())
        btn_row.add_widget(change_pin_btn)

        lock_btn = RoundedButton(
            text="Lock Vault Now",
            bg_color=COLOR_ACCENT,
            font_size="13sp",
            size_hint_x=0.45
        )
        lock_btn.bind(on_release=lambda x: self._lock_app())
        btn_row.add_widget(lock_btn)

        card.add_widget(btn_row)
        return card

    def _build_currency_card(self):
        card = Card(orientation="vertical", padding=[16, 14, 16, 14], spacing=12, size_hint_y=None, height=190)

        header_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=24)
        title = Label(
            text="Preferred Currency",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            halign="left",
            valign="middle"
        )
        title.bind(size=title.setter("text_size"))
        header_box.add_widget(title)

        self.currency_indicator = Label(
            text="Current: $",
            font_size="13sp",
            color=COLOR_PRIMARY,
            bold=True,
            halign="right",
            valign="middle"
        )
        self.currency_indicator.bind(size=self.currency_indicator.setter("text_size"))
        header_box.add_widget(self.currency_indicator)
        card.add_widget(header_box)

        grid = GridLayout(cols=3, spacing=8, size_hint_y=None, height=92)
        currencies = [
            ("$", "USD ($)"),
            ("€", "EUR (€)"),
            ("£", "GBP (£)"),
            ("¥", "JPY (¥)"),
            ("C$", "CAD (C$)"),
            ("A$", "AUD (A$)"),
        ]

        self.currency_buttons = {}
        for symbol, name in currencies:
            btn = RoundedButton(
                text=name,
                font_size="12sp",
                bg_color=COLOR_CARD_LIGHT,
                radius=[8, 8, 8, 8]
            )
            btn.bind(on_release=lambda inst, s=symbol: self._set_currency(s))
            self.currency_buttons[symbol] = btn
            grid.add_widget(btn)

        card.add_widget(grid)
        return card

    def _build_preferences_card(self):
        card = Card(orientation="vertical", padding=[16, 14, 16, 14], spacing=10, size_hint_y=None, height=110)

        title = Label(
            text="Privacy & Display",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=24,
            halign="left",
            valign="middle"
        )
        title.bind(size=title.setter("text_size"))
        card.add_widget(title)

        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=10)
        self.privacy_label = Label(
            text="Mask Balances on Dashboard",
            font_size="13sp",
            color=COLOR_TEXT_SECONDARY,
            halign="left",
            valign="middle"
        )
        self.privacy_label.bind(size=self.privacy_label.setter("text_size"))
        row.add_widget(self.privacy_label)

        self.privacy_toggle_btn = RoundedButton(
            text="Disabled",
            size_hint=(None, 1),
            width=110,
            font_size="12sp",
            bg_color=COLOR_CARD_LIGHT
        )
        self.privacy_toggle_btn.bind(on_release=lambda x: self._toggle_privacy())
        row.add_widget(self.privacy_toggle_btn)

        card.add_widget(row)
        return card

    def _build_data_info_card(self):
        card = Card(orientation="vertical", padding=[16, 14, 16, 14], spacing=8, size_hint_y=None, height=140)

        title = Label(
            text="Data & App Info",
            font_size="15sp",
            bold=True,
            color=COLOR_TEXT_PRIMARY,
            size_hint_y=None,
            height=24,
            halign="left",
            valign="middle"
        )
        title.bind(size=title.setter("text_size"))
        card.add_widget(title)

        self.stats_label = Label(
            text="Transactions: 0  |  Savings Goals: 0",
            font_size="13sp",
            color=COLOR_TEXT_SECONDARY,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        self.stats_label.bind(size=self.stats_label.setter("text_size"))
        card.add_widget(self.stats_label)

        info_sub = Label(
            text="Storage: 100% Offline Local JSON  |  Version: 1.0.0",
            font_size="12sp",
            color=COLOR_MUTED,
            size_hint_y=None,
            height=20,
            halign="left",
            valign="middle"
        )
        info_sub.bind(size=info_sub.setter("text_size"))
        card.add_widget(info_sub)

        return card

    def _build_danger_card(self):
        card = Card(
            orientation="vertical",
            padding=[16, 16, 16, 16],
            spacing=10,
            size_hint_y=None,
            height=130,
            border_color=(0.937, 0.267, 0.267, 0.4)
        )

        title = Label(
            text="Danger Zone",
            font_size="15sp",
            bold=True,
            color=COLOR_EXPENSE,
            size_hint_y=None,
            height=22,
            halign="left",
            valign="middle"
        )
        title.bind(size=title.setter("text_size"))
        card.add_widget(title)

        reset_btn = RoundedButton(
            text="Reset All Data & PIN",
            bg_color=COLOR_EXPENSE,
            text_color=(1, 1, 1, 1),
            size_hint_y=None,
            height=44,
            font_size="14sp",
            bold=True
        )
        reset_btn.bind(on_release=lambda x: self._prompt_first_reset())
        card.add_widget(reset_btn)

        return card

    # ========================== EVENT HANDLERS ==========================

    def on_pre_enter(self, *args):
        self.refresh_settings_view()

    def refresh_settings_view(self):
        settings = get_settings()
        current_cur = settings.get("currency", "$")
        self.currency_indicator.text = f"Current: {current_cur}"

        for symbol, btn in self.currency_buttons.items():
            if symbol == current_cur:
                btn.set_bg_color(COLOR_PRIMARY)
                btn.color = (1, 1, 1, 1)
            else:
                btn.set_bg_color(COLOR_CARD_LIGHT)
                btn.color = COLOR_TEXT_SECONDARY

        is_private = bool(settings.get("privacy_mode", False))
        if is_private:
            self.privacy_toggle_btn.text = "Enabled"
            self.privacy_toggle_btn.set_bg_color(COLOR_PRIMARY)
        else:
            self.privacy_toggle_btn.text = "Disabled"
            self.privacy_toggle_btn.set_bg_color(COLOR_CARD_LIGHT)

        tx_count = len(get_transactions())
        goals_count = len(get_goals())
        self.stats_label.text = f"Transactions: {tx_count}  |  Savings Goals: {goals_count}"

    def _set_currency(self, symbol):
        settings = get_settings()
        settings["currency"] = symbol
        save_settings(settings)
        self.refresh_settings_view()
        show_message("Currency Updated", f"Base currency set to '{symbol}'.")

    def _toggle_privacy(self):
        settings = get_settings()
        new_val = not bool(settings.get("privacy_mode", False))
        settings["privacy_mode"] = new_val
        save_settings(settings)
        self.refresh_settings_view()

    def _lock_app(self):
        app = App.get_running_app()
        if app and hasattr(app, "go"):
            app.go("pin_screen_0", direction="right")

    def _open_change_pin_dialog(self):
        dialog_content = BoxLayout(orientation="vertical", spacing=12, padding=[16, 16, 16, 16])

        curr_input = TextInput(
            hint_text="Current 4-digit PIN",
            password=True,
            input_filter="int",
            multiline=False,
            size_hint_y=None,
            height=44,
            background_normal="",
            background_active="",
            background_color=COLOR_CARD_LIGHT,
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_MUTED,
            padding=[10, 10, 10, 10],
            font_size="15sp"
        )
        new_input = TextInput(
            hint_text="New 4-digit PIN",
            password=True,
            input_filter="int",
            multiline=False,
            size_hint_y=None,
            height=44,
            background_normal="",
            background_active="",
            background_color=COLOR_CARD_LIGHT,
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_MUTED,
            padding=[10, 10, 10, 10],
            font_size="15sp"
        )
        confirm_input = TextInput(
            hint_text="Confirm new 4-digit PIN",
            password=True,
            input_filter="int",
            multiline=False,
            size_hint_y=None,
            height=44,
            background_normal="",
            background_active="",
            background_color=COLOR_CARD_LIGHT,
            foreground_color=COLOR_TEXT_PRIMARY,
            hint_text_color=COLOR_MUTED,
            padding=[10, 10, 10, 10],
            font_size="15sp"
        )

        dialog_content.add_widget(curr_input)
        dialog_content.add_widget(new_input)
        dialog_content.add_widget(confirm_input)

        btn_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=44)
        popup = Popup(
            title="Change 4-Digit Security PIN",
            title_size="16sp",
            title_color=COLOR_TEXT_PRIMARY,
            content=dialog_content,
            size_hint=(0.88, 0.45),
            auto_dismiss=False,
            separator_color=COLOR_PRIMARY
        )

        def on_cancel(inst):
            popup.dismiss()

        def on_save(inst):
            old_val = curr_input.text.strip()
            new_val = new_input.text.strip()
            conf_val = confirm_input.text.strip()

            if not verify_pin(old_val):
                show_message("Incorrect PIN", "Current PIN does not match. Please try again.")
                return

            if len(new_val) != 4 or not new_val.isdigit():
                show_message("Invalid PIN", "New PIN must be exactly 4 numerical digits.")
                return

            if new_val != conf_val:
                show_message("Mismatch", "New PIN and confirmation do not match.")
                return

            set_new_pin(new_val)
            popup.dismiss()
            show_message("Success", "Your 4-digit PIN has been successfully changed.")

        cancel_btn = RoundedButton(text="Cancel", bg_color=COLOR_CARD_LIGHT)
        cancel_btn.bind(on_release=on_cancel)
        btn_row.add_widget(cancel_btn)

        save_btn = RoundedButton(text="Save PIN", bg_color=COLOR_PRIMARY)
        save_btn.bind(on_release=on_save)
        btn_row.add_widget(save_btn)

        dialog_content.add_widget(btn_row)
        popup.open()

    # ========================== DOUBLE CONFIRMATION RESET ==========================

    def _prompt_first_reset(self):
        show_confirm(
            "Reset All Data?",
            "Are you sure you want to clear your local ledger, transactions, and savings goals?",
            on_confirm=self._prompt_second_reset
        )

    def _prompt_second_reset(self):
        show_confirm(
            "Final Warning",
            "This action is completely IRREVERSIBLE. All data and your PIN will be permanently deleted! Continue?",
            on_confirm=self._execute_full_reset
        )

    def _execute_full_reset(self):
        reset_all_data()
        app = App.get_running_app()

        def redirect():
            if app and hasattr(app, "go"):
                app.go("pin_screen_0", direction="right")

        show_message(
            "Data Cleared",
            "All records have been wiped. Please set up a new 4-digit PIN.",
            on_dismiss=redirect
        )
