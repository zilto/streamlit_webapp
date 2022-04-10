import json

import streamlit as st
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

from features import normalize_plays_coords, _game_seconds
from utils import parse_gamePk, get_metadata, game_to_df, get_highlight_title
from data_query import ApiEngine


def display_details(metadata_dict):
    data = {
        "Goals": [metadata_dict["home_goals"], metadata_dict["away_goals"]],
        "Shot": [metadata_dict["home_shots"], metadata_dict["away_shots"]],
        "Blocked": [metadata_dict["home_blocked"], metadata_dict["away_blocked"]],
        "Takeaways": [metadata_dict["home_takeaways"], metadata_dict["away_takeaways"]],
        "Giveaways": [metadata_dict["home_giveaways"], metadata_dict["away_giveaways"]],
        "Faceoff Win %": [metadata_dict["home_faceoff_win_percent"], metadata_dict["away_faceoff_win_percent"]],
        "Hit": [metadata_dict["home_hit"], metadata_dict["away_hit"]],
        "Penalty Infraction Minutes": [metadata_dict["home_pim"], metadata_dict["away_pim"]],
        "Powerplay %": [metadata_dict["home_powerplay_percent"], metadata_dict["away_powerplay_percent"]],
        "Powerplay Goals": [metadata_dict["home_powerplay_goals"], metadata_dict["away_powerplay_goals"]],
        "Powerplay Opportunities": [metadata_dict["home_powerplay_opportunities"], metadata_dict["away_powerplay_opportunities"]],
    }
    
    home_tri = metadata_dict["home_tri"]
    away_tri = metadata_dict["away_tri"]
    df = pd.DataFrame(data, columns=[f"{home_tri} (home)", f"{away_tri} (away)"])
    return df


def display_summary(game_json):
    metadata = get_metadata(game_json)
    
    text_block = f"""
    \n
    Datetime: {metadata["start_time"].split("T")[0]}\n
    Home: {metadata["home_name"]} ({metadata["home_tri"]})\n
    Away: {metadata["away_name"]} ({metadata["away_tri"]})\n
    Results: 
    """
    return text_block


def display_stats(game_json, player_id):
    key = "ID" + str(player_id).upper()
    
    if key in game_json["liveData"]["boxscore"]["teams"]["away"]["players"]:
        stats = game_json["liveData"]["boxscore"]["teams"]["away"]["players"][key]
        team = game_json["gameData"]["teams"]["away"]["triCode"]
    elif key in game_json["liveData"]["boxscore"]["teams"]["home"]["players"]:
        stats = game_json["liveData"]["boxscore"]["teams"]["home"]["players"][key]
        team = game_json["gameData"]["teams"]["home"]["triCode"]
        
    title = stats["person"]["fullName"] + " - " + stats["position"]["name"] + f" ({team})"
    stats_json = stats["stats"]["skaterStats"]
    stats_df = pd.DataFrame.from_dict(stats_json, orient="index")
    return title, stats_df


def get_recap_url(game_media):
    all_recaps = list(filter(lambda x: x["title"] == "Recap", game_media["media"]["epg"]))[0]
    recap = list(filter(lambda x: x["name"] == "FLASH_1200K_640X360", all_recaps["items"][0]["playbacks"]))[0]
    recap_url = recap["url"]
    return recap_url


def get_highlight_url(highlight):
    h = list(filter(lambda x: x["name"] == "FLASH_1200K_640X360", highlight["highlight"]["playbacks"]))[0]
    highlight_url = h["url"]
    return highlight_url


def display_shotmap(game_df):
    norm_df = normalize_plays_coords(game_df, side=False)
    
    fig = px.scatter(
        data_frame=norm_df,
        x="x_coord_norm",
        y="y_coord_norm",
        range_x=[-100,100],
        range_y=[-43,43],
        color="team_initiative_id",
        hover_data=["period_idx", "period_time", "shooter_name", "shot_type"],
        labels={
            "team_initiative_id": "Teams",
            "x_coord_norm": "X",
            "y_coord_norm": "Y",
            "period_idx": "Period",
            "period_time": "Period Time",
            "shooter_name": "Player",
            "shot_type": "Shot Type"
        },
        # color-blind friendly palette from https://mikemol.github.io/technique/colorblind/2018/02/11/color-safe-palette.html
        color_discrete_sequence=["#009E73", "#E69F00", "#CC79A7"]
    )
    
    fig.update_traces(
        marker=dict(
            size=8,
            line=dict(
                width=2,
                color="DarkSlateGrey"
            )
        )
    )
    
    fig.update_layout(
        xaxis_title=None,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
        ),
        yaxis_title=None,
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,
            showgrid=False,
            zeroline=False,
        )
    )
    
    fig.add_layout_image(
        dict(
            source="https://raw.githubusercontent.com/zilto/nice-play/main/src/assets/full_rink_c.png",
            xref="x",
            yref="y",
            x=-100,
            y=43,
            sizex=200,
            sizey=86,
            sizing="stretch",
            opacity=1,
            layer="below"
        )
    )
    
    return fig


def display_timeline(game_df):
    seconds = _game_seconds(game_df)
    color = game_df.team_initiative_id.copy()
    color.loc[game_df.event_type_id=="GOAL"] = "Goal"
    fig = px.scatter(
        data_frame=game_df,
        x=seconds,
        y="team_initiative_id",
        range_x=["00:00", "20:00"],
        color=color,
        hover_data=["event_type_id", "period_idx"],
        labels={
            "team_initiative_id": "Teams",
            "period_idx": "Game Period",
            "x": "Game Time (sec)",
            "event_type_id": "Event",
            "color": "Teams"
        },
        color_discrete_sequence=["#009E73", "#E69F00", "#CC79A7"],
        height=230
    )
    
    fig.update_layout(
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            tickmode="linear",
            tick0=0,
            dtick=300,
        ),
        yaxis_title=None,
        yaxis=dict(
            showgrid=False,
            zeroline=False,
        )
    )
    
    return fig


def page(): 
    api_engine = ApiEngine("./")
    with open("C:/.coding/hockey_webapp/hockey_webapp/demo_json/game_20202021_2020020001.json", "r") as f:
        game_json = json.load(f)
        
    with open("C:/.coding/hockey_webapp/hockey_webapp/demo_json/game_media.json", "r") as f:
        game_media = json.load(f)    
        
    game_summary = display_summary(game_json)

    with st.sidebar:
        st.text("")
        st.subheader("Select Game")

        year_select = st.selectbox("Select Year", options=[y for y in range(2021, 2020, -1)])
        gamePk_list = api_engine.get_all_season_gamePk(int(year_select))
        gamePk_select = 2021020001
        gamePk_select = st.selectbox("Select Game", options=gamePk_list, format_func=parse_gamePk)

        if st.button("Query Game"):
            game_json = api_engine.get_game(int(gamePk_select))
            game_media = api_engine.get_media(int(gamePk_select))
            game_summary = display_summary(game_json)

    ### 1.GAME RECAP ###
    st.subheader("Game Recap")     
    left_col, right_col = st.columns([1, 1])         
    with left_col:
        recap_url = get_recap_url(game_media)
        st.video(recap_url)
    with right_col:
        st.markdown(game_summary)
        
    ### 2.SHOTMAP ###
    st.subheader("Shotmap")  
    # st.info("In a hockey game, team switch sides each period. The shotmap displays the normalized coordinates, keeping each team on the same side the whole game.")
    shotmap_container = st.container()
    with shotmap_container:
        game_df = game_to_df(game_json)
        shotmap = display_shotmap(game_df)
        timeline = display_timeline(game_df)
        
        st.plotly_chart(shotmap, use_container_width=True)
        st.plotly_chart(timeline, use_container_width=True)
        
    ### 3.GOAL VIDEO ###
    
    highlights = [h for h in game_media["media"]["milestones"]["items"] if h["type"] in ["GOAL", "SHOT"]]
    highlight_select = st.selectbox("Select Media", options=highlights, format_func=get_highlight_title)
    
    highlight_url = get_highlight_url(highlight_select)
    st.video(highlight_url)
    st.write(highlight_select["highlight"]["description"])
    
    
    ### 4.STARS ###
    # stars_container = st.container()
    # with stars_container:
    #     st.subheader("Stars of the Game")
        
    #     star1_id = str(game_json["liveData"]["decisions"]["firstStar"]["id"])
    #     star2_id = str(game_json["liveData"]["decisions"]["secondStar"]["id"]),
    #     star3_id = str(game_json["liveData"]["decisions"]["thirdStar"]["id"]),
    #     star1_title, star1_stats = display_stats(game_json, star1_id)
    #     star2_title, star2_stats = display_stats(game_json, star2_id)
    #     star3_title, star3_stats = display_stats(game_json, star3_id)
    #     with st.expander("1st - " + star1_title):
    #         st.json(star1_stats)
    #     with st.expander("2nd - " + star2_title):
    #         st.json(star2_stats)
    #     with st.expander("3rd - " + star3_title):
    #         st.json(star3_stats)