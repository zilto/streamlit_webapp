import pandas as pd
import numpy as np


def normalize_plays_coords(plays_df, x_col="x_coord", y_col="y_coord", period=True, side=True):
    def normalize_period_coords(plays_df, x_col="x_coord", y_col="y_coord"):
        #mask for even periods
        mask = (plays_df["period_idx"]%2==0)
        plays_df.loc[mask, f"{x_col}_norm"] = -plays_df[f"{x_col}"]
        plays_df.loc[mask, f"{y_col}_norm"] = -plays_df[f"{y_col}"]
        return plays_df

    def normalize_side_coords(plays_df, x_col="x_coord", y_col="y_coord"):
        negative_side_df = plays_df.groupby(["gamePk", "team_initiative_id"]).filter(lambda x: x[f"{x_col}_norm"].mean() < 0)
        plays_df.loc[negative_side_df.index, f"{x_col}_norm"] = -negative_side_df[f"{x_col}_norm"]
        plays_df.loc[negative_side_df.index, f"{y_col}_norm"] = -negative_side_df[f"{y_col}_norm"]
        return plays_df
    
    plays_df[[f"{x_col}_norm", f"{y_col}_norm"]] = plays_df[[f"{x_col}", f"{y_col}"]].copy()
    if period:
        plays_df = normalize_period_coords(plays_df, x_col=x_col, y_col=y_col)
    if side:
        plays_df = normalize_side_coords(plays_df, x_col=x_col, y_col=y_col)
    return plays_df



def basic_features(plays_df):
    plays_df = normalize_plays_coords(plays_df)
    dist_from_net = _dist_from_net(plays_df)
    angle_from_net = _angle_from_net(plays_df)
    is_goal = _is_goal(plays_df)
    empty_net = _empty_net(plays_df)
           
    features_df = pd.concat([dist_from_net, angle_from_net, is_goal, empty_net], axis=1)
    return features_df


def _dist_from_net(plays_df):
    net_pos = np.array([100-11, 0])
    shot_vector = net_pos - plays_df[["x_coord_norm", "y_coord_norm"]]
    dist_from_net = np.linalg.norm(shot_vector, ord=2, axis=1)
    return pd.Series(dist_from_net, name="dist_from_net", index=plays_df.index)


def _angle_from_net(plays_df, x_col="x_coord", y_col="y_coord"):
    normalize_plays_coords(plays_df, x_col=x_col, y_col=y_col)
    net_pos = np.array([100-11, 0])
    shot_vector = net_pos - plays_df[[f"{x_col}_norm", f"{y_col}_norm"]]
    cos_angle = shot_vector @ net_pos / (np.linalg.norm(net_pos, ord=2) * np.linalg.norm(shot_vector, ord=2, axis=1))
    angle = np.degrees(np.arccos(cos_angle))
    
    plays_df["angle_from_net"] = pd.Series(angle, name="angle_from_net", index=plays_df.index)
    plays_df.loc[plays_df[f"{y_col}_norm"]<0, "angle_from_net"] = -plays_df.angle_from_net
    return pd.Series(plays_df.angle_from_net, name="angle_from_net", index=plays_df.index)


def _is_goal(plays_df):
    str_to_int = {"SHOT": 0, "GOAL": 1}
    is_goal = plays_df.event_type_id.replace(str_to_int)
    return pd.Series(is_goal, name="is_goal", index=plays_df.index)


def _empty_net(plays_df):
    return pd.Series(plays_df.empty_net_bool.astype(float), name="empty_net", index=plays_df.index)


def advanced_features(plays_df):
    plays_df = normalize_plays_coords(plays_df)
    
    subset_df = plays_df[["period_idx", "x_coord", "y_coord", "x_coord_norm", "y_coord_norm"]]
    
    seconds_elapsed = _game_seconds(plays_df)
    dist_from_net = _dist_from_net(plays_df)
    angle_from_net = _angle_from_net(plays_df)
    shot_type = _shot_type(plays_df)
    empty_net = _empty_net(plays_df)
    previous_event_type = _previous_event_type(plays_df)
    previous_x = _previous_x_coords(plays_df)
    previous_y = _previous_y_coords(plays_df)
    seconds_from_previous = _seconds_from_previous(plays_df)
    dist_from_previous = _dist_from_previous(plays_df)
    rebound = _is_rebound(plays_df)
    angle_change = _angle_change(plays_df)
    speed = dist_from_previous / seconds_from_previous 
    speed = pd.Series(speed, name="speed", index=plays_df.index).replace([np.inf, -np.inf, np.nan], 0)
    
    features_df = pd.concat([
        seconds_elapsed,
        subset_df,
        dist_from_net,
        angle_from_net,
        shot_type,
        empty_net,
        previous_event_type, 
        previous_x, previous_y,
        seconds_from_previous,
        dist_from_previous,
        rebound,
        angle_change,
        speed,
        ],
        axis=1
    )
    
    return features_df


def _game_seconds(plays_df):
    plays_df["period_time"] = pd.to_datetime(plays_df["period_time"], format="%M:%S")
    plays_df["period_seconds"] = (plays_df["period_time"] - pd.to_datetime("1900-01-01")).dt.total_seconds()
    
    regular_period_mask = (plays_df["period_idx"] - 1 <= 3)
    plays_df.period_seconds.loc[regular_period_mask] += (plays_df["period_idx"] - 1) * 1200
    
    regular_overtime_mask = (plays_df["period_idx"] - 1 > 3) & (plays_df["game_type"] != "P")
    plays_df.period_seconds.loc[regular_overtime_mask] += (plays_df["period_idx"] - 1) * 1200
    plays_df.period_seconds.loc[regular_overtime_mask] += (plays_df["period_idx"] - 4) * 300
    
    playoff_overtime_mask = (plays_df["period_idx"] - 1 > 3) & (plays_df["game_type"] == "P")
    plays_df.period_seconds.loc[playoff_overtime_mask] += (plays_df["period_idx"] - 1) * 1200
    plays_df.period_seconds.loc[playoff_overtime_mask] += (plays_df["period_idx"] - 4) * 1200
    
    # if plays_df["period_idx"] - 1 <= 3:
    #     previous_periods_seconds = (plays_df["period_idx"] - 1) * 1200
    # if plays_df["period_idx"] - 1 > 3:
    #     previous_periods_seconds = 3 * 1200 # 3 full periods
    #     n_overtime_completed = plays_df["period_idx"] - 4
    #     if plays_df["game_type"] == "P":
    #         previous_periods_seconds += n_overtime_completed * 1200 # 20 min overtime during playoffs
    #     else:
    #         previous_periods_seconds += n_overtime_completed * 300 # 3 min overtime during playoffs
    
    #seconds_elapsed = np.round(period_seconds + previous_periods_seconds)
    return pd.Series(np.round(plays_df.period_seconds), name="seconds_elapsed", index=plays_df.index)


def _shot_type(plays_df):
    return pd.get_dummies(plays_df.shot_type)


def _previous_event_type(plays_df):
    period_mask = (plays_df.period_idx == plays_df.previous_event_period)
    previous_event = pd.Series(plays_df.loc[period_mask, "previous_event_type"], name="previous_event_type", index=plays_df.index)
    previous_event = previous_event.replace({"GAME_OFFICIAL":"OTHER", "PERIOD_END":"OTHER", "PERIOD_READY":"OTHER", "CHALLENGE":"OTHER"})
    return pd.get_dummies(previous_event)


def _previous_x_coords(plays_df):
    period_mask = (plays_df.period_idx == plays_df.previous_event_period)
    previous_x = plays_df.loc[period_mask, "previous_event_x_coord"].fillna(0)
    return pd.Series(previous_x, name="previous_x_coord", index=plays_df.index)


def _previous_y_coords(plays_df):
    period_mask = (plays_df.period_idx == plays_df.previous_event_period)
    previous_y = plays_df.loc[period_mask, "previous_event_y_coord"].fillna(0)
    return pd.Series(previous_y, name="previous_y_coord", index=plays_df.index)


def _seconds_from_previous(plays_df):
    plays_df["period_time"] = pd.to_datetime(plays_df["period_time"], format="%M:%S")
    plays_df["previous_event_period_time"] = pd.to_datetime(plays_df["previous_event_period_time"], format="%M:%S")
    period_mask = (plays_df.period_idx == plays_df.previous_event_period)
    time_diff = (plays_df.loc[period_mask,"period_time"] - plays_df.loc[period_mask,"previous_event_period_time"]).dt.total_seconds()
    return pd.Series(np.round(time_diff), name="seconds_from_previous", index=plays_df.index)


def _dist_from_previous(plays_df):
    period_mask = (plays_df.period_idx == plays_df.previous_event_period)
    movement_vector = plays_df.loc[period_mask, ["x_coord", "y_coord"]] - plays_df.loc[period_mask, ["previous_event_x_coord", "previous_event_y_coord"]].values
    dists = np.linalg.norm(movement_vector, ord=2, axis=1)
    return pd.Series(dists, name="dist_from_previous", index=movement_vector.index)


def _is_rebound(plays_df):
    period_mask = (plays_df.period_idx == plays_df.previous_event_period)
    rebound_mask = (plays_df.previous_event_type.isin(["SHOT", "GOAL"]))
    plays_df["rebound"] = np.where(period_mask & rebound_mask, 1, 0)
    return pd.Series(plays_df.rebound, name="rebound", index=plays_df.index)


def _angle_change(plays_df):
    plays_df = normalize_plays_coords(plays_df, x_col="previous_event_x_coord", y_col="previous_event_y_coord")
    current_angle = _angle_from_net(plays_df).copy()
    previous_angle = _angle_from_net(plays_df, x_col="previous_event_x_coord", y_col="previous_event_y_coord").rename("prev_angle").copy()
    plays_df["rebound"] = _is_rebound(plays_df)
    plays_df.loc[plays_df.rebound==1, "angle_change"] = current_angle - previous_angle
    plays_df.angle_change = plays_df.angle_change.fillna(0)
    return pd.Series(plays_df.angle_change, name="angle_change", index=plays_df.index)
