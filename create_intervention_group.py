#mcandrew

import pandas as pd
from datetime import datetime
import numpy as np

import boto3
import streamlit as st

if __name__ == "__main__":

    AWS_S3_BUCKET         = "wmm-2025"
    AWS_ACCESS_KEY_ID     = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    usernames_dataset = pd.read_csv("./dataset/intervention_group.csv")
    s3_client.put_object(Bucket=AWS_S3_BUCKET, Key="intervention_group.csv", Body=usernames_dataset.to_csv(index=False).encode('utf-8'))
    
