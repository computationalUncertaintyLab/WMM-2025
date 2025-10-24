#mcandrew

import pandas as pd
from datetime import datetime
import numpy as np

import boto3
import streamlit as st

if __name__ == "__main__":

    AWS_S3_BUCKET = "wmm-2025"
    AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    d = pd.DataFrame({ "Actor"   :["exp626",'thm220']
                      ,"Audience":["thm220",'gms221']
                      ,"infection_intervention":[1,1]
                      ,"success"               :[1,1]
                      ,"intervention_value"    :[np.nan,np.nan]
                      ,'intervention_type'     :[-1,-1]
                      ,"timestamp"             :[datetime.now().strftime("%Y-%m-%d %H:%M:%S"),datetime.now().strftime("%Y-%m-%d %H:%M:%S")]})

    s3_client.put_object(Bucket=AWS_S3_BUCKET, Key="interactions.csv", Body=d.to_csv(index=False).encode('utf-8'))

