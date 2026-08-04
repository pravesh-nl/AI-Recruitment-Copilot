from streamlit_option_menu import option_menu
import streamlit as st


def show_sidebar():

    with st.sidebar:

        st.markdown("## 🤖 Recruitment Copilot")

        selected = option_menu(
            menu_title=None,
            options=[
                "Dashboard",
                "Resume Upload",
                "Candidates",
                "Job Postings",
                "Analytics",
                "Settings"
            ],
            icons=[
                "speedometer2",
                "cloud-upload",
                "people",
                "briefcase",
                "bar-chart",
                "gear"
            ],
            default_index=1
        )

    return selected