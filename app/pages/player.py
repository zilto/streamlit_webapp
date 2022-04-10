import json

import streamlit as st
import pandas as pd

from data_query import ApiEngine
from utils import parse_year_to_season


@st.cache
def generate_roster_df():
    with open("C:/.coding/hockey_webapp/hockey_webapp/demo_json/team_rosters.json", "r") as f:
        ROSTER = json.load(f)
    
    records = []
    for team in ROSTER["teams"]:
        team_id = team["id"]
        team_name = team["teamName"]
        for player in team["roster"]["roster"]:
            player_record = dict(
                team_id=team_id,
                team_name=team_name,
                player_id=player["person"]["id"],
                player_name=player["person"]["fullName"],
                position=player["position"]["name"],
            )
            records.append(player_record)
    
    return pd.DataFrame.from_records(records)


def get_player_years(year_by_year):
    years_json = year_by_year["stats"][0]
    assert "splits" in years_json
    
    years_dict = {}
    for split in years_json["splits"]:
        # 133 is the NHL league ID
        if split["league"].get("id", -1) == 133:
            season = split["season"]
            years_dict[season] = f'{season[:4]} - {split["team"]["name"]}'
    
    return years_dict
            

def page():  
    api_engine = ApiEngine("./")
    
    with st.sidebar:
        ROSTER_DF = generate_roster_df()
        
        st.text("")
        st.subheader("Select Player")
       
        position_filter = st.multiselect("Filter by Position", options=sorted(ROSTER_DF.position.unique()))
        team_filter = st.multiselect("Filter by Team", options=sorted(ROSTER_DF.team_name.unique()))
        
        if position_filter and team_filter:
            player_list = sorted(ROSTER_DF.loc[
                    (ROSTER_DF["position"].isin(position_filter)) & (ROSTER_DF["team_name"].isin(team_filter)),
                    "player_name"]
            )
        elif position_filter:
            player_list = sorted(ROSTER_DF.loc[ROSTER_DF["position"].isin(position_filter), "player_name"])
        elif team_filter:
            player_list = sorted(ROSTER_DF.loc[ROSTER_DF["team_name"].isin(team_filter), "player_name"])
        else:
            player_list = sorted(ROSTER_DF["player_name"])
            
        player_select = st.selectbox("Select Player", options=player_list)
        
        if st.button("Query Player"):
            st.write(player_select)
    
    st.subheader("Player Summary")
    
    st.subheader("Player Drilldown")
    #year_by_year = api_engine.get_player_year_by_year(ROSTER_DF.loc[ROSTER_DF.player_name==player_select, "player_id"].values[0])
    with open("C:/.coding/hockey_webapp/hockey_webapp/demo_json/player_yearbyyear.json", "r") as f:
        year_by_year = json.load(f)
    years_dict = get_player_years(year_by_year)
    st.selectbox("Select Year", options=list(years_dict.values()))
    
    