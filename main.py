import sqlite3

import database

from kivymd.app import MDApp
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem
from kivymd.uix.screen import MDScreen
from kivy.properties import NumericProperty, StringProperty
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window

Window.size = (300,600)

class RootManager(ScreenManager):
    pass

class StartScreen(MDScreen):

    def search_players(self, search):
        resultlist = database.execute_select_query("SELECT Name FROM Spieler WHERE INSTR(Name, ?)", (search, ))
        self.update_playerlist(resultlist)

    def update_playerlist(self, namelist = None):
        self.ids.playerlist.clear_widgets()
        if namelist == None:
            namelist = database.execute_select_query("SELECT Name FROM Spieler ORDER BY Name ASC", ())

        for name in namelist:
            self.ids.playerlist.add_widget(
                OneLineListItem(
                    text=f"{name[0]}"
                )
            )

class NewPlayerScreen(MDScreen):

    def save_player(self, name, year):
        database.execute_query("INSERT INTO Spieler (Name, Geburtsjahr) VALUES (?, ?)", (name, year))
        app = MDApp.get_running_app()
        app.rootmanager.ids.start_screen.update_playerlist()
        app.rootmanager.switch_to(app.rootmanager.ids.start_screen)

class NewMatchScreen(MDScreen):

    def start_analysis(self, player, opponent, date):
        playerid = database.execute_select_query("SELECT SpielerID FROM Spieler WHERE Name = ?",(player,))
        playerid = playerid[0]
        database.execute_query("INSERT INTO Match (SpielerID, Gegnername, Matchtag) Values (? , ?, ?)",(playerid[0], opponent , date,))
        MDApp.get_running_app().rootmanager.current = "analysisscreen"
        MDApp.get_running_app().rootmanager.ids.analysis_screen.on_start()
        MDApp.get_running_app().rootmanager.ids.analysis_screen.ids.player_name.text = player
        MDApp.get_running_app().rootmanager.ids.analysis_screen.ids.opponent_name.text = opponent

class AnalysisScreen(MDScreen):
    player_points = NumericProperty(0)
    opponent_points = NumericProperty(0)
    touch_counter = NumericProperty(0)
    positionlist = ["bh_fc", "m_fc", "fh_fc", "bh_mc", "m_mc", "fh_mc", "bh_bc", "m_bc", "fh_bc"]
    placementlist = ["bh_fc_opp", "m_fc_opp", "fh_fc_opp", "bh_mc_opp", "m_mc_opp", "fh_mc_opp", "bh_bc_opp", "m_bc_opp", "fh_bc_opp"]
    errorlist = ["b_out_opp", "b_out", "l_out", "r_out", "net"]
    set_exist = 0


    def on_start(self):
        self.curr_match = database.execute_select_query("SELECT max(MatchID) FROM Match", ())[0]
        self.curr_player = database.execute_select_query("SELECT SpielerID FROM Match WHERE MatchID = ?", (self.curr_match[0],))[0]

    def new_set(self):
        self.player_points = 0
        self.opponent_points = 0
        database.execute_query("INSERT INTO Satz (SpielerID, MatchID) VALUES (?, ?)",
                               (self.curr_player[0], self.curr_match[0]))
        self.curr_set = database.execute_select_query("SELECT max(SatzID) FROM Satz", ())[0]
        if self.set_exist < 3:
            self.ids.player_score.add_widget(MDLabel(text=str(self.player_points)))
            self.ids.opp_score.add_widget(MDLabel(text=str(self.opponent_points)))

        self.set_exist += 1

    def button_pressed(self, button_name):
        print(self.player_points)
        if self.set_exist != 0:

            if self.touch_counter == 0:
                database.execute_query("INSERT INTO Ballwechsel (Gegner_punkte, Spieler_punkte) Values (?, ?)",
                                       (self.opponent_points, self.player_points))
                self.curr_rally = database.execute_select_query("SELECT max(BallwechselID) FROM Ballwechsel", ())[0]
                if button_name in self.positionlist:
                    database.execute_query(
                        "INSERT INTO Punkt (SpielerID, MatchID, SatzID, BallwechselID, Spieler_pos) VALUES (?, ?, ?, ?, ?)",
                        (self.curr_player[0], self.curr_match[0], self.curr_set[0], self.curr_rally[0], button_name))
                    self.touch_counter += 1

                elif button_name in self.placementlist or self.errorlist:
                    database.execute_query(
                        "INSERT INTO Punkt (SpielerID, MatchID, SatzID, BallwechselID) VALUES (?, ?, ?, ?)",
                        (self.curr_player[0], self.curr_match[0], self.curr_set[0], self.curr_rally[0]))
                    self.player_points += 1
                    self.touch_counter = 0


            elif self.touch_counter == 1:

                if button_name in self.placementlist:
                    database.execute_query("UPDATE Punkt SET Schlag_pos = ? WHERE BallwechselID = ?",
                                           (button_name, self.curr_rally[0]))
                    self.touch_counter = 0

                elif button_name in self.errorlist or self.positionlist:
                    database.execute_query("UPDATE Punkt SET Schlag_pos = ? WHERE BallwechselID = ?",
                                           (button_name, self.curr_rally[0]))
                    self.opponent_points += 1
                    self.touch_counter = 0

class Court(MDBoxLayout):
    pass

class AreaButton(Button):
    pass

class MainApp(MDApp):

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.rootmanager = RootManager()
        self.build_playerlist()
        return self.rootmanager


    def build_playerlist(self):
        playerlist = database.execute_select_query("SELECT Name FROM Spieler ORDER BY Name ASC", ())

        for playername in playerlist:
            self.rootmanager.ids.start_screen.ids.playerlist.add_widget(
                OneLineListItem(
                    text=f"{playername[0]}"
                )
            )


MainApp().run()