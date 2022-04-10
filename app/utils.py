import streamlit as st
import pandas as pd

def parse_gamePk(gamePk):
    """
    https://statsapi.web.nhl.com/api/v1/gameTypes
    First 4 digits give the season
    (ie. 2017 for the 2017-2018 season)

    Next 2 digits give the type of game
    - 01 = preseason (PR)
    - 02 = regular season (R)
    - 03 = playoffs (P)
    - 04 = all-star (A)

    Final 4 digits give the specific game number.
    for PR, the 2nd digit gives the round of the playoffs,
    the 3rd digit specifies the matchup,
    and the 4th digit specifies the game (out of 7).
    """
    game_type = str(gamePk)[4:6]
    game_id = str(gamePk)[6:10]
    
    game_type_conversion = {
        "01": "Preseason",
        "02": "Regular",
        "03": "Playoffs",
        "04": "All-star"
    }
    
    return f"{game_type_conversion[game_type]}-{game_id}"

def parse_year_to_season(start_year):
        return str(start_year) + str(start_year+1)


def play_json_to_play_dict(play_json):
    # returns nothing if the event is not of type SHOT or GOAL
    if play_json["result"]["eventTypeId"] not in ["SHOT", "GOAL"]:
        return None
        
    shooter_id = None
    shooter_name = None
    goalie_id = None
    goalie_name = None
    # logic for attributing shooter and goalie name (if exists)
    if play_json.get("players"):
        for player in play_json["players"]:
            if player["playerType"] in ["Shooter", "Scorer"]:
                shooter_id = str(player["player"]["id"])
                shooter_name = player["player"]["fullName"]
            if player["playerType"] == "Goalie":
                goalie_id = str(player["player"]["id"])
                goalie_name = player["player"]["fullName"]
                
    strength = None
    if play_json["result"].get("strength"):
        strength = play_json["result"]["strength"]["code"]
    
    play_dict = {
        "event_idx": play_json["about"]["eventIdx"],
        "event_stats_id": play_json["about"]["eventId"],
        "event_type_id": play_json["result"]["eventTypeId"],
        "period_idx": play_json["about"]["period"],
        "period_type": play_json["about"]["periodType"],
        "game_time": play_json["about"]["dateTime"],
        "period_time": play_json["about"]["periodTime"],
        "shot_type": play_json["result"].get("secondaryType"),
        "team_initiative_id": play_json["team"].get("triCode"),
        "team_initiative_name": play_json["team"].get("name"),
        "x_coord": play_json["coordinates"].get("x"),
        "y_coord": play_json["coordinates"].get("y"),
        "shooter_id": shooter_id,
        "shooter_name": shooter_name,
        "goalie_id": goalie_id,
        "goalie_name": goalie_name,
        "strength": strength,
        "empty_net_bool": play_json["result"].get("emptyNet")
    }
    
    return play_dict


def augment_with_previous_event(all_plays_list, plays_dict_list):
    augmented_plays_dict = []
    for play_dict in plays_dict_list:
        current_event_idx = play_dict["event_idx"]
        previous_event_idx = current_event_idx - 1
        
        previous_event = {
            "previous_event_idx": previous_event_idx,
            "previous_event_stats_id": None,
            "previous_event_period": None,
            "previous_event_period_time": None,
            "previous_event_time": None,
            "previous_event_type": None,
            "previous_event_x_coord": None,
            "previous_event_y_coord": None,
        }
        
        for play_json in all_plays_list:
            if play_json["about"]["eventIdx"] == previous_event_idx:
                previous_event["previous_event_type"] = play_json["result"]["eventTypeId"]
                previous_event["previous_event_stats_id"] = play_json["about"]["eventId"]
                previous_event["previous_event_period"] = int(play_json["about"]["period"])
                previous_event["previous_event_period_time"] = play_json["about"]["periodTime"]
                previous_event["previous_event_time"] = play_json["about"]["dateTime"]
                previous_event["previous_event_x_coord"] = play_json["coordinates"].get("x")
                previous_event["previous_event_y_coord"] = play_json["coordinates"].get("y")
                
                break
            
        play_dict.update(previous_event)
        augmented_plays_dict.append(play_dict)
        
    return augmented_plays_dict


def game_json_to_plays_list(game_json, augment=False):
    all_plays_list = game_json["liveData"]["plays"]["allPlays"]
    plays_dict_list = list(filter(None, [play_json_to_play_dict(play) for play in all_plays_list]))
    if augment:
        plays_dict_list = augment_with_previous_event(all_plays_list, plays_dict_list)
    
    game_metadata = {
        "gamePk": game_json["gameData"]["game"]["pk"],
        "game_season": game_json["gameData"]["game"]["season"],
        "game_type": game_json["gameData"]["game"]["type"],
        "game_start_time": game_json["gameData"]["datetime"].get("dateTime")
    }
    
    plays_with_metadata = []
    for play_dict in plays_dict_list:
        play_dict.update(game_metadata)
        plays_with_metadata.append(play_dict)
        
    return plays_with_metadata

@st.cache
def get_metadata(game_json):
    metadata_dict = {
        # game metadata
        "start_time": game_json["gameData"]["datetime"]["dateTime"],
        "venue": game_json["gameData"]["venue"]["name"],

        # away team
        "away_name": game_json["gameData"]["teams"]["away"]["name"],
        "away_tri": game_json["gameData"]["teams"]["away"]["triCode"],
        "away_goals": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["goals"],
        #"away_pim": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["pim"],
        "away_shots": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["shots"],
        #"away_powerplay_percent": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["powerPlayPercentage"],
        #"away_powerplay_goals": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["powerPlayGoals"],
        #"away_powerplay_opportunities": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["powerPlayOpportunities"],
        #"away_faceoff_win_percent": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["faceOffWinPercentage"],
        "away_blocked": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["blocked"],
        "away_takeaways": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["takeaways"],
        "away_giveaways": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["giveaways"],
        #"away_hit": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["hits"],
        
        # home team
        "home_name": game_json["gameData"]["teams"]["home"]["name"],
        "home_tri": game_json["gameData"]["teams"]["home"]["triCode"],
        "home_goals": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["goals"],
        #"home_pim": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["pim"],
        "home_shots": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["shots"],
        #"home_powerplay_percent": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["powerPlayPercentage"],
        #"home_powerplay_goals": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["powerPlayGoals"],
        #"home_powerplay_opportunities": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["powerPlayOpportunities"],
        #"home_faceoff_win_percent": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["faceOffWinPercentage"],
        "home_blocked": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["blocked"],
        "home_takeaways": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["takeaways"],
        "home_giveaways": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["giveaways"],
        #"home_hit": game_json["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["hits"],
        
        # general play stats
        "n_plays": len(game_json["liveData"]["plays"]["allPlays"]),
        "n_plays_period1": len(game_json["liveData"]["plays"]["playsByPeriod"][0]["plays"]),
        "n_plays_period2": len(game_json["liveData"]["plays"]["playsByPeriod"][1]["plays"]),
        "n_plays_period3": len(game_json["liveData"]["plays"]["playsByPeriod"][2]["plays"]),
        "n_scoring_plays": len(game_json["liveData"]["plays"]["scoringPlays"]),
        "n_penalty_plays": len(game_json["liveData"]["plays"]["penaltyPlays"]),
        "has_shoutout": game_json["liveData"]["linescore"]["hasShootout"],
        
        # stars of the game
        "first_star_id": str(game_json["liveData"]["decisions"]["firstStar"]["id"]),
        "first_star_name": game_json["liveData"]["decisions"]["firstStar"]["fullName"],
        "second_star_id": str(game_json["liveData"]["decisions"]["secondStar"]["id"]),
        "second_star_name": game_json["liveData"]["decisions"]["secondStar"]["fullName"],
        "third_star_id": str(game_json["liveData"]["decisions"]["thirdStar"]["id"]),
        "third_star_name": game_json["liveData"]["decisions"]["thirdStar"]["fullName"],
    }
    
    return metadata_dict


def get_highlight_title(highlight):
    idx = highlight["ordinalNum"]
    title = highlight["highlight"].get("title")
    return f"{idx} - {title}"

def game_to_df(game_json, augment=False):
    game_plays_list = game_json_to_plays_list(game_json, augment=augment)
    game_plays_df = pd.DataFrame.from_records(game_plays_list)
    return game_plays_df