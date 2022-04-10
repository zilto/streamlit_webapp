import streamlit as st

from pages import home, game, player, team
from app_multipage import MultiApp

st.set_page_config(
    page_title="Nice Play - NHL Data Exploration",
    page_icon=":ice_hockey_stick_and_puck:",
    layout="wide",
    initial_sidebar_state="expanded"
)


app = MultiApp()

side = st.sidebar

side.header("Page Navigation")
st.title("Nice play: NHL Data Exploration")
app.add_app("Home", home.page)
app.add_app("Game Explorer", game.page)
app.add_app("Player Drilldown",player.page)
app.add_app("Team Records", team.page)
app.run()

side.text("")
side.text("")
side.text("built by Thierry Jean")

