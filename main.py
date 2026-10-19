from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from screens.pin_screen_0 import PinScreenScreen0
from screens.dashboard_screen_1 import DashboardScreenScreen1
from screens.add_transaction_screen_2 import AddTransactionScreenScreen2
from screens.transaction_history_screen_3 import TransactionHistoryScreenScreen3
from screens.reports_screen_4 import ReportsScreenScreen4
from screens.savings_goals_screen_5 import SavingsGoalsScreenScreen5
from screens.add_goal_screen_6 import AddGoalScreenScreen6
from screens.settings_screen_7 import SettingsScreenScreen7

# Configure window background default to deep slate
Window.clearcolor = (0.059, 0.090, 0.165, 1.0)


class FinVaultApp(App):
    def __init__(self, **kwargs):
        super(FinVaultApp, self).__init__(**kwargs)
        self.title = "FinVault"
        self.history = []
        self.sm = None

    def build(self):
        self.sm = ScreenManager(transition=SlideTransition(duration=0.2))

        # Add planned screens in designated order
        screens = [
            ("pin_screen_0", PinScreenScreen0),
            ("dashboard_screen_1", DashboardScreenScreen1),
            ("add_transaction_screen_2", AddTransactionScreenScreen2),
            ("transaction_history_screen_3", TransactionHistoryScreenScreen3),
            ("reports_screen_4", ReportsScreenScreen4),
            ("savings_goals_screen_5", SavingsGoalsScreenScreen5),
            ("add_goal_screen_6", AddGoalScreenScreen6),
            ("settings_screen_7", SettingsScreenScreen7),
        ]

        for route_name, screen_cls in screens:
            instance = screen_cls(name=route_name)
            self.sm.add_widget(instance)

        return self.sm

    def go(self, route_name, direction="left"):
        if not self.sm or not self.sm.has_screen(route_name):
            return
        current = self.sm.current
        if current != route_name:
            self.history.append(current)
            self.sm.transition.direction = direction
            self.sm.current = route_name

    def go_back(self):
        if not self.sm:
            return
        if self.history:
            prev = self.history.pop()
            if self.sm.has_screen(prev):
                self.sm.transition.direction = "right"
                self.sm.current = prev
        else:
            # Default fallback when stack empty
            if self.sm.current != "dashboard_screen_1" and self.sm.current != "pin_screen_0":
                self.sm.transition.direction = "right"
                self.sm.current = "dashboard_screen_1"


if __name__ == "__main__":
    FinVaultApp().run()
