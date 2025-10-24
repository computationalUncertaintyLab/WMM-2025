#mcandrew

import sys
import numpy as np
import pandas as pd
import streamlit as st


def attach_WMM_data():
    AWS_S3_BUCKET = "wmm-2025"
    AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
    if 'dataset' not in st.session_state:
        st.session_state.dataset = pd.read_csv(f"s3://{AWS_S3_BUCKET}/interactions.csv"
                                              ,storage_options={"key"   : AWS_ACCESS_KEY_ID,"secret": AWS_SECRET_ACCESS_KEY})
    if 'intervention_group' not in st.session_state:
        intervention_group = pd.read_csv(f"s3://{AWS_S3_BUCKET}/intervention_group.csv"
                                                          ,storage_options={"key"   : AWS_ACCESS_KEY_ID,"secret": AWS_SECRET_ACCESS_KEY})
        st.session_state.intervention_group = intervention_group.username.unique()


def page_info():
    st.title("🔐 Login")
    st.markdown('''

                ## The Watermelon Meow Meow Outbreak
                * To infect, navigate to "User Input" (*most important page*)
                * To view contacts, navigate to "Contact network infections"
                * To view cases over time, navigate to "Cases over time"


                ### Research Consent
                This research study aims to generate a contact network of successful transmissions of the watermelon-meow-meow pathogen.
                We hypothesize that a student-driven, real-time outbreak of a **fictitious** pathogen will improve student comprehension of course material. 

                **What data is collected from me?**: We collect, and will present on this app, your Lehigh username (i.e. the three letter and three number combination from your Lehigh email address. For example, thm220).

                **How will my data be used?**: We plan to build a contact network over time that will present Lehigh usernames. This will be public and presented on the `Contact Network Infections' page.
                In addition, your connections to others will be used in class to simulate an outbreak to understand the mathematics of the spread of disease over a contact network. 


                **Contacts and Questions**: The Institutional Review Board (IRB) for the protection of human research participants at Lehigh University has reviewed and approved this study. If you have questions about the research study itself, please contact the Investigators: Gabrielle String (gms221@lehigh.edu), Jeffrey Olimpo (jto224@lehigh.edu), and Thomas McAndrew (mcandrew@lehigh.edu). If you have questions about your rights or would simply like to speak with someone other than the research team about the questions or concerns, please contact the IRB at (610) 758-2871 or inirb@lehigh.edu. All reports or correspondence will be kept confidential.

                **Statement of Consent:** I have read the above information. I have had the opportunity to ask questions and have my questions answered. By adding my Lehigh Username, I consent to participate in this study.

            ''')


def show():
    attach_WMM_data()

    with st.container(border=True):
        col = st.columns(1)
        with col[0]:
            page_info()
            
            #--Username
            username = st.text_input("Please enter your username (the letters and numbers before @lehigh.edu)")

            if st.button("Login"):
                if username.strip() != "":
                    st.session_state["logged_in"]          = True
                    st.session_state["username"]           = username
                    
                    if username in st.session_state.intervention_group:
                        st.session_state.interventionalist = True
                    else:
                        st.session_state.interventionalist  = False

                        

                    #--attach WMM personal information
                    st.success("Thank you for login")
                    st.switch_page("pages/user_input.py")

                else:
                    st.warning("Please enter a username.")


if __name__ == "__main__":
    show()
    



