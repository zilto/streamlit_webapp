# Reference: https://github.com/dmf95/nhl-expansion-twitter-app/blob/main/app_multipage.py
"""Frameworks for running multiple Streamlit applications as a single app.
"""
import streamlit as st

class MultiApp:
    """Framework for combining multiple streamlit applications.
    It is also possible keep each application in a separate file.
        import foo
        import bar
        app = MultiApp()
        app.add_app("Foo", foo.app)
        app.add_app("Bar", bar.app)
        app.run()
    """
    def __init__(self):
        self.pages = []

    def add_app(self, title, func):
        self.pages.append({
            "title": title,
            "function": func
        })

    def run(self):
        app = st.sidebar.selectbox(
            'Choose a page',
            self.pages,
            format_func=lambda app: app['title']
        )

        app['function']()
