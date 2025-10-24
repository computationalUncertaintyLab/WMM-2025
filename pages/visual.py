
#mcandrew

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

def contact_network():
    from pyvis.network import Network
    import networkx as nx
    
    # Create a local copy to avoid modifying session state
    interactions = st.session_state["dataset"].copy()

    # Create a directed graph from the dataset
    G = nx.DiGraph()
    for _, row in interactions.iterrows():
        if row.Actor not in G.nodes:
            if row.infection_intervention and row.success:
                G.add_node(row.Actor, infected=1)
            elif row.infection_intervention and not row.success:
                G.add_node(row.Actor, infected=2)
            else:
                G.add_node(row.Actor, infected=0)

        if row.Audience not in G.nodes or row.infection_intervention:
            if row.infection_intervention and row.success:
                G.add_node(row.Audience, infected=1)
            elif row.infection_intervention and not row.success:
                G.add_node(row.Audience, infected=2)
            else:
                G.add_node(row.Audience, infected=0)
        G.add_edge(row['Actor'], row['Audience'])

        # Set background to white and default node color to black
        net = Network(height='740px', width='100%', bgcolor='white', font_color='black', directed=True)

        for node in G.nodes:
            if G.nodes[node]["infected"] == 2:
                color = "gray"
            elif G.nodes[node]["infected"] == 1:
                color = "red"
            else:
                color = "blue"
            net.add_node(node, label=node, color=color)

        for edge in G.edges:
            net.add_edge(edge[0], edge[1], width=2, color = "black")

    net.save_graph('network.html')

    HtmlFile = open('network.html', 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    st.components.v1.html(source_code, height=750)

    return G

def search_user(search_username=None, G=None):
    """Search for a user and display their infection subgraph"""
    from pyvis.network import Network
    
    if not search_username or G is None:
        return
    
    # Get the dataset
    interactions = st.session_state["dataset"].copy()
    
    # Check if user exists in the network
    if search_username not in G.nodes:
        st.warning(f"User '{search_username}' not found in the network.")
        return
    
    # Find primary contacts (nodes infected by the searched user)
    primary_contacts = [node for node in G.successors(search_username)]
    
    # Find secondary contacts (nodes infected by primary contacts)
    secondary_contacts = [neighbor for p in primary_contacts for neighbor in G.successors(p) if neighbor != search_username]
    
    # Create subgraph
    subgraph_nodes = set([search_username] + primary_contacts + secondary_contacts)
    subgraph = G.subgraph(subgraph_nodes)
    
    # Calculate statistics
    infected_count = len(primary_contacts)
    infection_data = interactions[
        (interactions['Actor'] == search_username) & 
        (interactions['infection_intervention'] == 1) & 
        (interactions['success'] == 1)
    ]
    first_infection = infection_data['timestamp'].min() if not infection_data.empty else "No infections"
    
    st.markdown(f"**User: {search_username}**")
    st.markdown(f"- Number of people directly infected: **{infected_count}**")
    st.markdown(f"- First infection date: **{first_infection}**")
    
    # Create visualization
    net = Network(height='500px', width='100%', bgcolor='white', font_color='black', directed=True)
    
    # Add nodes with colors
    for node in subgraph.nodes:
        if node == search_username:
            color = 'blue'
        elif node in primary_contacts:
            color = 'red'
        else:
            color = 'gray'
        net.add_node(node, label=node, color=color)
    
    # Add edges
    for edge in subgraph.edges:
        net.add_edge(edge[0], edge[1], width=2, color='black')
    
    # Save and display
    net.save_graph('subgraph.html')
    
    HtmlFile = open('subgraph.html', 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    st.components.v1.html(source_code, height=520)
    
    st.markdown("**Color Coding in the Subgraph:**")
    st.markdown("- **Blue**: The searched user")
    st.markdown("- **Red**: Users directly infected by the searched user (primary contacts)")
    st.markdown("- **Gray**: Users infected by the primary contacts (secondary contacts)")
    
def display_data():
    st.markdown("### Data Dictionary")
    st.markdown("""
    **Column Descriptions:**
    - **Actor**: The person initiating the action (infector or interventionist)
    - **Audience**: The person receiving the action (infectee or intervention recipient)
    - **infection_intervention**: Type of event (1 = infection attempt, 0 = intervention)
    - **success**: Whether the event was successful (1 = successful, 0 = unsuccessful/contact only)
    - **intervention_value**: The effectiveness value of the intervention (NaN for infections)
    - **intervention_type**: The specific type of intervention applied (-1 for infections)
    - **timestamp**: Date and time when the event occurred
    """)
    st.dataframe(st.session_state.dataset)

def show_cumulative_plots():
    """Display cumulative infection and intervention plots"""
    import plotly.graph_objects as go
    import plotly.express as px
    
    # Get the dataset and create a local copy to avoid modifying session state
    interactions = st.session_state.get("dataset", pd.DataFrame()).copy()
    
    if interactions.empty:
        st.warning("No data available yet.")
        return
    
    # Convert timestamp to datetime (local copy only)
    interactions['datetime'] = pd.to_datetime(interactions['timestamp'])
    interactions['hour'] = interactions['datetime'].dt.floor('H')  # Round to nearest hour
    
    # Create two columns for the visualizations
    col1, col2 = st.columns(2)
    
    # Column 1: Cumulative Infections Over Time (per hour)
    with col1:
        st.subheader("📊 Cumulative Infections Over Time")
        
        # Filter for successful infections (infection_intervention=1 and success=1)
        successful_infections = interactions[
            (interactions['infection_intervention'] == 1) & 
            (interactions['success'] == 1)
        ].copy()
        
        if not successful_infections.empty:
            # Group by hour and count infections
            infections_per_hour = successful_infections.groupby('hour').size().reset_index(name='count')
            infections_per_hour = infections_per_hour.sort_values('hour')
            
            # Calculate cumulative sum
            infections_per_hour['cumulative'] = infections_per_hour['count'].cumsum()
            
            # Create bar chart using plotly
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=infections_per_hour['hour'],
                y=infections_per_hour['cumulative'],
                marker_color='black',
                name='Cumulative Infections'
            ))
            
            fig.update_layout(
                xaxis_title="Time (Hour)",
                yaxis_title="Cumulative Infections",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No successful infections recorded yet.")
    
    # Column 2: Cumulative Interventions Over Time (per intervention type)
    with col2:
        st.subheader("📈 Cumulative Interventions Over Time")
        
        # Filter for interventions (infection_intervention=0)
        interventions_only = interactions[interactions['infection_intervention'] == 0].copy()
        
        if not interventions_only.empty:
            # Get unique intervention types
            intervention_types = interventions_only['intervention_type'].unique()
            intervention_types = [it for it in intervention_types if pd.notna(it)]
            
            if intervention_types:
                # Create figure
                fig = go.Figure()
                
                # Add a trace for each intervention type
                for intervention_type in intervention_types:
                    # Filter for this specific intervention type
                    type_data = interventions_only[
                        interventions_only['intervention_type'] == intervention_type
                    ].copy()
                    
                    # Group by hour and count interventions
                    interventions_per_hour = type_data.groupby('hour').size().reset_index(name='count')
                    interventions_per_hour = interventions_per_hour.sort_values('hour')
                    
                    # Calculate cumulative sum
                    interventions_per_hour['cumulative'] = interventions_per_hour['count'].cumsum()
                    
                    # Add scatter + line trace
                    fig.add_trace(go.Scatter(
                        x=interventions_per_hour['hour'],
                        y=interventions_per_hour['cumulative'],
                        mode='lines+markers',
                        name=str(intervention_type),
                        line=dict(width=2),
                        marker=dict(size=8)
                    ))
                
                fig.update_layout(
                    xaxis_title="Time (Hour)",
                    yaxis_title="Cumulative Interventions",
                    showlegend=True,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    ),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No valid intervention types found.")
        else:
            st.info("No interventions recorded yet.")

def infection_viz():
    st.title('Intervention Analytics Dashboard')
    st.markdown('Track infections and interventions over time.')
    
    # Show the cumulative plots first
    show_cumulative_plots()
    
    st.markdown("---")
    
    # Then show the contact network
    st.title('Contact Network')
    st.markdown('Visualize how people have infected each other within Lehigh University.')
    G = contact_network()

    with st.expander("### Search for a User"):
        user = st.text_input("Enter a username to see their infection details")
        search_user(user, G)

    with st.expander("See data that generated this network"):
        display_data()

def intervention_viz():
    st.title('Intervention Analytics Dashboard')
    st.markdown('Track infections and interventions over time.')
    
    # Show the cumulative plots
    show_cumulative_plots()

def refresh_data_from_s3():
    """Refresh the dataset from S3 to get the latest data"""
    try:
        import boto3
        from io import BytesIO
        
        AWS_S3_BUCKET = "wmm-2025"
        AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
        AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
        
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Read the latest data from S3
        s3_obj = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="interactions.csv")
        st.session_state.dataset = pd.read_csv(BytesIO(s3_obj['Body'].read()))
        
    except Exception as e:
        print(f"Warning: Failed to refresh data from S3: {str(e)}")
        # If refresh fails, continue with existing session data

def show():
    #--LOGIN GATE
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("🚫 You must log in first.")
        st.stop()   # Prevents rest of the page from rendering
    
    # Refresh data from S3 to get the latest updates
    refresh_data_from_s3()
    
    with st.container(border=True):
        cols = st.columns(1, border=False)

        with cols[0]:
            if st.session_state["interventionalist"]:
                intervention_viz()
            else:
                infection_viz()
            
if __name__ == "__main__":
    show()


                
