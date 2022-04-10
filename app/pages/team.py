import streamlit as st

import json

import streamlit as st
import pandas as pd

from data_query import ApiEngine
from utils import parse_year_to_season


@st.cache
def generate_teams_df(teams_json):    
    records = []
    for team in teams_json["teams"]:
        team_record = dict(
            team_id=team["id"],
            team_name=team["teamName"],
            team_full_name=team["name"],
            team_triCode=team["abbreviation"],
        )
        records.append(team_record)
    
    return pd.DataFrame.from_records(records)
            

def page():  
    api_engine = ApiEngine("./")
    
    with st.sidebar:
        teams_json = api_engine.get_teams()
        TEAMS_DF = generate_teams_df(teams_json)
        
        st.text("")       
        team_select = st.selectbox("Select Team", options=sorted(TEAMS_DF.team_full_name))

        if st.button("Query Team"):
            st.write(team_select)
    
    st.subheader("Team Drill Down")
    stats_json = api_engine.get_team_stats(str(TEAMS_DF.loc[TEAMS_DF.team_full_name==team_select, "team_id"].values[0]))
    st.json(stats_json)
    
    