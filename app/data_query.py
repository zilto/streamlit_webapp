import requests
import json

import pandas as pd
import streamlit as st


# class to interact with the API
class ApiEngine:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    @staticmethod
    def _start_year_to_season_string(start_year):
        """pass start_year, return a string to select a season (i.e., 2017 -> 20172018)"""
        return str(start_year) + str(start_year+1)
        
    @staticmethod
    def query_api(endpoint, params=None):
        """query API endpoint"""
        # base url of the API
        url = f"https://statsapi.web.nhl.com/api/v1/{endpoint}"
        r = requests.get(url, params=params, timeout=3)
        # check if the HTTP request is valid
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Could not reach API endpoint:\n'{url}'")
        return r.json()

    @st.cache
    def get_season_schedule(self, start_year):
        """query API for the schedule of the year (to get valid gamePk)"""
        season_string = self._start_year_to_season_string(start_year)
        season_response = self.query_api("schedule", params={"season": season_string})
        return season_response
        
    # query API for a specific game
    @st.cache
    def get_game(self, gamePk):
        game_response = self.query_api(f"game/{gamePk}/feed/live")
        return game_response
    
    def get_media(self, gamePk):
        game_media = self.query_api(f"game/{gamePk}/content")
        return game_media
    
    @st.cache
    def get_player_year_by_year(self, player_id):
        year_by_year = self.query_api(f"people/{player_id}/stats?stats=yearByYear")
        return year_by_year
    
    @st.cache
    def get_teams(self):
        teams = self.query_api(f"teams")
        return teams
    
    @st.cache
    def get_team_stats(self, team_id):
        team_stats = self.query_api(f"teams?expand=team.stats&teamId={team_id}")
        return team_stats

    @st.cache
    def get_all_season_gamePk(self, start_year):
        """get list of valid gamePk from season schedule"""
        season_schedule = self.get_season_schedule(start_year)
        gamePk_list = []
        for date in season_schedule["dates"]:
            for game in date["games"]:
                gamePk_list.append(game["gamePk"])
        return gamePk_list
  