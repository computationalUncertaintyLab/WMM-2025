import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import boto3
from io import BytesIO

def get_s3_client():
    """Get configured S3 client"""
    try:
        AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
        AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
        
        return boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
    except Exception as e:
        print(f"Error creating S3 client: {str(e)}")
        return None

def show_most_recent_report(username, reports_dir):
    """Display the most recent report submission for this user from S3"""
    AWS_S3_BUCKET = "wmm-2025"
    s3_client = get_s3_client()
    
    if s3_client is None:
        return
    
    try:
        # Read the log file from S3
        log_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="reports/report_submissions.csv")
        log_df = pd.read_csv(BytesIO(log_obj['Body'].read()))
        
        user_submissions = log_df[log_df['username'] == username]
        
        if not user_submissions.empty:
            # Get the most recent submission
            user_submissions = user_submissions.sort_values('timestamp', ascending=False)
            recent = user_submissions.iloc[0]
            
            filename = recent['filename']
            filesize = recent['filesize_kb']
            timestamp = recent['timestamp']
            s3_key = f"reports/{filename}"
            
            # Try to get the file from S3
            try:
                pdf_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
                pdf_data = pdf_obj['Body'].read()
                
                # Display the most recent report
                with st.container(border=True):
                    st.subheader("📌 Your Most Recent Report")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**File:** {filename}")
                        st.caption(f"Size: {filesize:.2f} KB | Uploaded: {timestamp}")
                    
                    with col2:
                        st.download_button(
                            label="⬇️ Download",
                            data=pdf_data,
                            file_name=filename,
                            mime="application/pdf",
                            key="download_recent"
                        )
                    
                    # Display PDF preview
                    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                
                st.markdown("---")
            except Exception as e:
                print(f"Error loading PDF from S3: {str(e)}")
                st.warning("Could not load the most recent report.")
                
    except s3_client.exceptions.NoSuchKey:
        # No log file exists yet
        pass
    except Exception as e:
        print(f"Error reading report log from S3: {str(e)}")

def show():
    # Login gate
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("🚫 You must log in first.")
        st.stop()
    
    # Check if user is in intervention group
    if not st.session_state["interventionalist"]:
        st.error("🚫 This page is only accessible to students in the intervention group.")
        st.stop()
    
    st.title("📄 Report Upload")
    st.markdown("Upload your intervention report as a PDF file.")
    
    # Get username from session
    username = st.session_state["username"]
    
    # Show most recent report
    show_most_recent_report(username, None)
    
    # File uploader
    with st.container(border=True):
        st.subheader("Upload Your Report")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload your intervention report in PDF format"
        )
        
        if uploaded_file is not None:
            # Display file details
            st.info(f"📎 File: {uploaded_file.name}")
            st.info(f"📊 Size: {uploaded_file.size / 1024:.2f} KB")
            
            # Submit button
            if st.button("Submit Report", type="primary"):
                try:
                    # Create filename with username and timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{username}_{timestamp}.pdf"
                    
                    # Save to S3
                    AWS_S3_BUCKET = "wmm-2025"
                    s3_client = get_s3_client()
                    
                    if s3_client is None:
                        st.error("❌ Could not connect to storage service.")
                        return
                    
                    # Upload PDF to S3
                    s3_key = f"reports/{filename}"
                    s3_client.put_object(
                        Bucket=AWS_S3_BUCKET,
                        Key=s3_key,
                        Body=uploaded_file.getbuffer(),
                        ContentType='application/pdf'
                    )
                    
                    st.success(f"✅ Report successfully uploaded! File saved as: {filename}")
                    
                    # Log the submission (this will also save to S3)
                    log_submission(username, filename, uploaded_file.size)
                    
                except Exception as e:
                    st.error(f"❌ Error uploading file: {str(e)}")
    
    # Show previous submissions
    st.markdown("---")
    show_previous_submissions(username)

def log_submission(username, filename, filesize):
    """Log report submission to S3"""
    AWS_S3_BUCKET = "wmm-2025"
    s3_client = get_s3_client()
    
    if s3_client is None:
        print("Could not connect to S3 for logging")
        return
    
    # Create log entry
    log_entry = {
        "username": username,
        "filename": filename,
        "filesize_kb": filesize / 1024,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        # Try to read existing log from S3
        log_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="reports/report_submissions.csv")
        log_df = pd.read_csv(BytesIO(log_obj['Body'].read()))
        log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
    except s3_client.exceptions.NoSuchKey:
        # Log file doesn't exist yet, create new one
        log_df = pd.DataFrame([log_entry])
    except Exception as e:
        print(f"Error reading log from S3: {str(e)}")
        log_df = pd.DataFrame([log_entry])
    
    # Save updated log to S3
    try:
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key="reports/report_submissions.csv",
            Body=log_df.to_csv(index=False).encode('utf-8'),
            ContentType='text/csv'
        )
    except Exception as e:
        print(f"Error saving log to S3: {str(e)}")

def show_previous_submissions(username):
    """Display previous report submissions for this user with download options from S3"""
    AWS_S3_BUCKET = "wmm-2025"
    s3_client = get_s3_client()
    
    if s3_client is None:
        st.info("Could not connect to storage service.")
        return
    
    try:
        # Read the log file from S3
        log_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="reports/report_submissions.csv")
        log_df = pd.read_csv(BytesIO(log_obj['Body'].read()))
        
        user_submissions = log_df[log_df['username'] == username]
        
        if not user_submissions.empty:
            st.subheader("📋 Your Previous Submissions")
            
            # Display each submission with a download button
            for idx, row in user_submissions.iterrows():
                filename = row['filename']
                filesize = row['filesize_kb']
                timestamp = row['timestamp']
                s3_key = f"reports/{filename}"
                
                # Create a container for each submission
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**📄 {filename}**")
                        st.caption(f"Size: {filesize:.2f} KB | Uploaded: {timestamp}")
                    
                    with col2:
                        # Try to get file from S3
                        try:
                            pdf_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
                            pdf_data = pdf_obj['Body'].read()
                            
                            st.download_button(
                                label="⬇️ Download",
                                data=pdf_data,
                                file_name=filename,
                                mime="application/pdf",
                                key=f"download_{idx}"
                            )
                        except Exception as e:
                            print(f"Error loading file {filename}: {str(e)}")
                            st.warning("File not found")
        else:
            st.info("No previous submissions found.")
    except s3_client.exceptions.NoSuchKey:
        st.info("No previous submissions found.")
    except Exception as e:
        print(f"Error reading submissions: {str(e)}")
        st.info("No previous submissions found.")

if __name__ == "__main__":
    show()

