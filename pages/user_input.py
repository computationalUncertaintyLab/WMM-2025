
import streamlit as st
import pandas as pd

from streamlit_player import st_player
from datetime import datetime, timedelta
import boto3

from streamlit_autorefresh import st_autorefresh

# Email validation function
def validate_input(email):
    import re   
    pattern = r'^[A-Za-z]+\d+$'
    pattern2 = r'^[A-Za-z]+\d+[A-Za-z]+$'
    return re.match(pattern, email) or re.match(pattern2, email)

def save_dataset_to_csv_and_s3(new_row_df):
    """Save new row to dataset in S3 with concurrency protection"""
    # Read the latest data from S3, append the new row, and save back
    # This prevents race conditions when multiple users submit simultaneously
    
    try:
        AWS_S3_BUCKET         = "wmm-2025"
        AWS_ACCESS_KEY_ID     = st.secrets["AWS_ACCESS_KEY_ID"]
        AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
        
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Read the current data from S3 (get the latest version)
        from io import BytesIO
        s3_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="interactions.csv")
        latest_dataset = pd.read_csv(BytesIO(s3_obj['Body'].read()))
        
        # Append the new row
        updated_dataset = pd.concat([latest_dataset, new_row_df], ignore_index=True)
        
        # Upload the updated dataset to S3
        s3_client.put_object(Bucket=AWS_S3_BUCKET, Key="interactions.csv", Body=updated_dataset.to_csv(index=False).encode('utf-8'))
        print(f"Successfully uploaded to S3: {AWS_S3_BUCKET}/interactions.csv")
        
        # Update session state with the latest data
        st.session_state.dataset = updated_dataset
        
    except Exception as e:
        print(f"Warning: Failed to upload to S3: {str(e)}")
        # Don't fail the whole operation if S3 upload fails




def infection_email(audience, actor, success=True):
    """Send infection notification email using OAuth 2.0"""
    import base64
    from email.mime.text import MIMEText
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    FROM = "thm220@lehigh.edu"
    TO = f"{audience}@lehigh.edu"
    
    if success:
        subject = "You were infected with Watermelon Meow Meow"
        body = f"""You have been infected with Watermelon Meow Meow!

You have been Infected by: {actor}

Instructions

1. You can infect students, staff, or professors, anyone with a lehigh account. You are also allowed to infect more than one person at a time. The only rule is that you need to be INPERSON with the individual(s). 
2. Open up this link https://wmm-2025.streamlit.app/ and login with your Lehigh username (the letters and numbers before @lehigh.edu).
3. Navigate to “User Input”
4. You should explain that lehigh usernames will be included in a public facing app.
5. Watch together the 1-min video.
6. Add your name to the Infector textbox, the person you are infecting to the “Infectee” text box and press submit.

- The WMM Team
"""
    else:
        subject = "Watermelon Meow Meow - Contact Attempt"
        body = f"""Someone attempted to infect you with Watermelon Meow Meow!

Contact from: {actor}

Good news - you were NOT infected this time! However, you are still at risk.

Please visit https://wmm-2025.streamlit.app/ to view your status.

Stay safe!

- The WMM Team
"""

    try:
        # Get OAuth credentials from Streamlit secrets
        credentials = Credentials(
            token=None,
            refresh_token=st.secrets["gmail_refresh_token"],
            client_id=st.secrets["gmail_client_id"],
            client_secret=st.secrets["gmail_client_secret"],
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        
        # Refresh the access token
        credentials.refresh(Request())
        
        # Build Gmail API service
        service = build('gmail', 'v1', credentials=credentials)
        
        # Create message
        message = MIMEText(body)
        message['to'] = TO
        message['from'] = FROM
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes())
        email_message = {'raw': raw.decode()}
        
        # Send message
        service.users().messages().send(userId="me", body=email_message).execute()
        print(f"Email successfully sent to {TO}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def add_user_data_to_database( actor, audience , infection_or_intervention = None, intervention_type = "Infection" , intervention_data = None):
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    from time import sleep
    from io import BytesIO

    # Refresh dataset from S3 to get latest data before validation
    try:
        AWS_S3_BUCKET = "wmm-2025"
        AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
        AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
        
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        s3_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="interactions.csv")
        st.session_state.dataset = pd.read_csv(BytesIO(s3_obj['Body'].read()))
    except Exception as e:
        print(f"Warning: Could not refresh data from S3: {str(e)}")
        # Continue with existing session data if refresh fails

    interactions              = st.session_state.dataset
    infection_or_intervention = 1 if infection_or_intervention else 0

    #--INFECTION------------------------------------------------------------------------------------------------------------
    if infection_or_intervention:
        if audience and actor:  # Check if not null
            if audience == actor:
                st.error("The audience and actor usernames cannot be the same. Please enter different usernames.")
            elif audience.lower() == "exp626":
                st.error("The username 'exp626' cannot be used as the audience.")
            else:
                valid_audience = validate_input(audience)
                valid_actor    = validate_input(actor)

                if not valid_audience:
                    st.error("Invalid input for your Lehigh Email credentials. Please follow the specified format.")
                elif not valid_actor:
                    st.error("Invalid input for the Lehigh Email credentials. Please follow the specified format.")

                else:
                    time_right_now               = datetime.now()
                    last_interaction_between_two = interactions.loc[ (interactions.Actor==actor) & (interactions.Audience==audience) , "timestamp"]
                    if len(last_interaction_between_two)>0:
                        last_interaction_between_two = sorted(last_interaction_between_two.values)[-1]

                        if ((time_right_now - datetime.strptime(last_interaction_between_two,"%Y-%m-%d %H:%M:%S")).seconds / (60)) < 1.:
                            st.warning(f"An event between {actor} and {audience} has taken place under a minute. There is a 60 second cool down between events of the same pair.")
                            return

                    #--Check if actor is contagious
                    if actor not in interactions.loc[(interactions.infection_intervention==1) & (interactions.success==1),"Audience"].unique():
                        st.error(f"{actor} is not eligible to infect others as they have not been infected yet.")
                        return 

                    #--Check if the audience has already been infected
                    successful_infections = interactions.loc[ (interactions.infection_intervention==1) & (interactions.success==1),'Audience' ].unique()
                    if audience in successful_infections:
                        st.warning(f"{audience} has already been infected in this game. Get out there and infect more people!")
                        return 

                    #--Attmept an infection event
                    interventions_applied_to_audience = interactions.loc[ (interactions.Audience == audience) & (interactions.infection_intervention==0) ] #<-- This is to remove times that person was contacte and never infected
                    INFECTION_BASELINE = 0.50 #<--this is the baseline probability of infection
                    
                    intervention = INFECTION_BASELINE
                    print(interventions_applied_to_audience)
                    if len(interventions_applied_to_audience) > 0:
                        intervention = INFECTION_BASELINE*np.prod(1. - interventions_applied_to_audience.intervention_value.values)

                    print(interventions_applied_to_audience.intervention_value.values)
                    print(intervention)

                    print(f"Intervention: {intervention}")
                    if np.random.random() < intervention:
                        #--Add new INFECTION record
                        current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        new_row = {     "Actor"                  :[actor]
                                       , "Audience"              :[audience]
                                       , "infection_intervention":[infection_or_intervention]
                                       , "success"               :[1]
                                       , "intervention_value"    :[INFECTION_BASELINE]
                                       , "intervention_type"     :[intervention_type]
                                       , "timestamp"             :[current_date_time]}

                        st.success(f"Thank you for submitting your information to WMM. The user {audience} was infected!")
                        
                        # Send infection email to the infected user
                        infection_email(audience, actor, success=True)

                    else:
                        #--Add new CONTACT record
                        current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        new_row = {      "Actor"                  :[actor]
                                       , "Audience"               :[audience]
                                       , "infection_intervention" :[1]         
                                       , "success"                :[0]
                                       , "intervention_value"     :[np.nan]
                                       , "intervention_type"      :[intervention_type]
                                       , "timestamp"              :[current_date_time]}
                        st.success(f"Thank you for submitting your information to WMM. The user {audience} was *NOT* infected!")
                        
                        # Send contact attempt email to the audience
                        infection_email(audience, actor, success=False)
                        
                    #--UPDATE state and write out (with concurrency protection)
                    new_row_df = pd.DataFrame(new_row)
                    save_dataset_to_csv_and_s3(new_row_df)
        else:
            st.error("One or both of the fields is missing input. Please ensure both emails are entered correctly.")
    #--INTERVENTION------------------------------------------------------------------------------------------------------------
    else:
       
        effectiveness_data = intervention_data[intervention_type].dropna()
        if effectiveness_data is None:
            st.error(f"The intervention type {intervention_type} is not valid. Please select a valid intervention type.")
            return
        effectiveness_data = effectiveness_data.values
        from scipy.stats import gaussian_kde

        print(effectiveness_data)
        kde = gaussian_kde(effectiveness_data/10.)


        if audience and actor:  # Check if not null
            if audience.lower() == "exp626":
                st.error("The username 'exp626' cannot be used as the audience.")
                return
                
            valid_audience = validate_input(audience)

            audience_interventions = interactions.loc[(interactions.Audience==audience) & (interactions.infection_intervention==0)]

            #--is the audience member already infected?
            audience_infected      = interactions.loc[ (interactions.Audience==audience) & (interactions.infection_intervention==1) & (interactions.success==1)]
            if len(audience_infected)>0:
                audience_infected=1
            else:
                audience_infected=0
            
            if not valid_audience:
                st.error("Invalid input for your Lehigh Email credentials. Please follow the specified format.")
            else:
                #--Have they already had this intervention type?
                if intervention_type in audience_interventions.intervention_type.unique():
                    st.warning(f"The user, {audience}, has already engaged with this intervention.")
                
                #--Check if the audience has already been infected
                elif audience_infected:
                    st.warning(f"{audience} has already been infected. Interventions are too late!")

                else:

                    intervention_value_random = np.clip( kde.resample(1)[0][0],0,1)
                    print(intervention_value_random)
                    
                    #--Add new intervention record
                    current_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_row = {       "Actor"                 :[actor]
                                    , "Audience"              :[audience]
                                    , "infection_intervention":[infection_or_intervention]
                                    , "success"               :[1]
                                    , "intervention_value"    :[ intervention_value_random ]
                                    , "intervention_type"     :[intervention_type]
                                    , "timestamp"             :[current_date_time]}

                    #--UPDATE state and write out (with concurrency protection)
                    new_row_df = pd.DataFrame(new_row)
                    save_dataset_to_csv_and_s3(new_row_df)

                    st.success("Thank you for submitting your information to WMM2. This intervention event has been stored successfully!")
        else:
            st.error("One or both of the fields is missing input. Please ensure both emails are entered correctly.")

def infection_page():
    infection_intervention=1
    with st.container(border=True):
        col = st.columns(1)
        with col[0]:
            st.title('Add an infectious event')
            st.markdown('''Include your Lehigh username in the box titled **infector** and include the Lehigh username of the person that you infected in the **infectee** box.
            A Lehigh username is the letters and numbers before @lehigh.edu. For example, the Lehigh username for thm220@lehigh.edu is thm220.''')

            # URL of the YouTube video to embed
            st_player('https://www.youtube.com/watch?v=ZSRfbByt4uk')

        cols = st.columns(2,border=False)
        with cols[0]:
            infectorEmail = st.text_input("Infector (i am the one who is infecting someone)", key="infectorEmail", value = st.session_state["username"] , help = "Put your username here if you infected someone ")
            infectorEmail = infectorEmail.lower().strip()
        with cols[1]:
            infecteeEmail = st.text_input("Infectee (i am going to be infected)", key="infecteeEmail", placeholder = "ABC123", help = "Put your username here if you were infected")
            infecteeEmail = infecteeEmail.lower().strip()

        cols = st.columns(1, border=False)
        with cols[0]:
            st.markdown('By pressing submit, you consent that your Lehigh username will appear on this public website.')

            if st.button('Submit'):
                add_user_data_to_database(infectorEmail, infecteeEmail, infection_or_intervention=1, intervention_type = -1)

def intervention_page():
    infection_intervention=0

    try:
        AWS_S3_BUCKET         = "wmm-2025"
        AWS_ACCESS_KEY_ID     = st.secrets["AWS_ACCESS_KEY_ID"]
        AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
        
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Read the current data from S3 (get the latest version)
        from io import BytesIO
        s3_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="intervention_effectiveness.csv")
        intervention_effectiveness_data = pd.read_csv(BytesIO(s3_obj['Body'].read()))
    except Exception as e:
        print(f"Warning: Could not load intervention data from S3: {str(e)}")
        st.error("Could not load intervention options. Please try again later.")
        return

    intervention_names = intervention_effectiveness_data.columns.tolist()

    interventions = {intervention_name: intervention_name for intervention_name in intervention_names}

    with st.container(border=True):
        col = st.columns(1)
        with col[0]:
            intervention_implemented = st.selectbox("What intervention did you experience?"
                                                    , options = list(interventions.values()))
            audienceEmail = st.text_input("My Lehigh username", key="audienceEmail", placeholder = "ABC123", help = "Put your username here if you recieved this intervention.")
            audienceEmail = audienceEmail.lower().strip()

            if st.button('Submit'):
                add_user_data_to_database(intervention_implemented
                , audienceEmail
                , infection_or_intervention=infection_intervention
                , intervention_type = intervention_implemented
                , intervention_data = intervention_effectiveness_data)

def show():

    #--LOGIN GATE
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("🚫 You must log in first.")
        st.stop()   # Prevents rest of the page from rendering
    

    if 'page_load_time' not in st.session_state:
        st.session_state.page_load_time = datetime.now()
        st.session_state.submit_enabled = False

    # Calculate the elapsed time since the page was loaded
    elapsed_time = datetime.now() - st.session_state.page_load_time

    with st.container(border=True):
        infection_intervention = st.segmented_control("**What action do you want to perform?**"
                                                      , options={"Infect":True, "Intervene":False}
                                                      , default="Infect"
                                                      , label_visibility="visible")

    #--PAGE STRUCTURE
    if infection_intervention == "Infect":
        infection_page()
        
    else:
        intervention_page()

if __name__ == "__main__":
    show()

