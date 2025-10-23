
#mcandrew

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

def contact_network():
    from pyvis.network import Network
    import networkx as nx
    
    interactions = st.session_state["dataset"]

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

def search_user(search_user=None):
    def create_subgraph(G, search_user):

        if search_user in G.nodes:
            # Find primary contacts (nodes infected by the searched user)
            primary_contacts = [node for node in G.successors(search_user)]
            # Find secondary contacts (nodes infected by primary contacts)
            secondary_contacts = [neighbor for p in primary_contacts for neighbor in G.successors(p) if neighbor != search_user]

            subgraph_nodes = set([search_user] + primary_contacts + secondary_contacts)
            subgraph = G.subgraph(subgraph_nodes)
            return subgraph, primary_contacts
        else:
            return None, []

    # Display search results and subgraph
    if search_user:
        subgraph, primary_contacts = create_subgraph(G, search_user)
        if subgraph:
            infected_count = df[df['Infector'] == search_user].shape[0]
            infection_dates = df[df['Infector'] == search_user]['Timestamp']
            first_infection = infection_dates.min() if not infection_dates.empty else "No infections"

            st.markdown(f"**User: {search_user}**")
            st.markdown(f"- Number of people infected: **{infected_count}**")
            st.markdown(f"- First infection date: **{first_infection}**")

            # Assign colors to nodes
            node_colors = {search_user: 'blue'}
            for node in primary_contacts:
                node_colors[node] = 'red'
            for node in subgraph.nodes:
                if node not in node_colors:
                    node_colors[node] = 'gray'

            # Visualize subgraph
            subgraph_net = create_pyvis_network(subgraph, node_colors)
            subgraph_net.save_graph('subgraph.html')

            display_pyvis_network('subgraph.html')

            st.markdown("**Color Coding in the Subgraph:**")
            st.markdown("- **Blue**: The searched user")
            st.markdown("- **Red**: Users directly impacted by the searched user (primary contacts)")
            st.markdown("- **Gray**: Users related to the primary contacts (secondary contacts)")
        else:
            st.markdown(f"User '{search_user}' not found in the network.")
    
def display_data():
    st.dataframe(st.session_state.dataset)

def infection_viz():
    st.title('Contact Network')
    st.markdown('Visualize how people have infected each other within Lehigh University.')
    contact_network()

    with st.expander("### Search for a User"):
        user = st.text_input("Enter a username to see their infection details")
        search_user(user)

    with st.expander("See data that generated this network"):
        display_data()

def intervention_viz():
    st.title('Intervention Analytics Dashboard')
    st.markdown('Track infections and interventions over time.')
    
    # Get the dataset
    interactions = st.session_state.get("dataset", pd.DataFrame())
    
    if interactions.empty:
        st.warning("No data available yet.")
        return
    
    # Convert timestamp to datetime
    interactions['date'] = pd.to_datetime(interactions['timestamp']).dt.date
    
    # 1. Bar chart of successful infections per day
    st.subheader("📊 Successful Infections Per Day")
    
    # Filter for successful infections (infection_intervention=1 and success=1)
    successful_infections = interactions[
        (interactions['infection_intervention'] == 1) & 
        (interactions['success'] == 1)
    ]
    
    if not successful_infections.empty:
        infections_per_day = successful_infections.groupby('date').size().reset_index(name='count')
        infections_per_day.columns = ['Date', 'Successful Infections']
        
        st.bar_chart(infections_per_day.set_index('Date'))
    else:
        st.info("No successful infections recorded yet.")
    
    st.markdown("---")
    
    # 2. Bar charts per intervention type
    st.subheader("📈 Interventions Per Day by Type")
    
    # Filter for interventions (infection_intervention=0)
    interventions_only = interactions[interactions['infection_intervention'] == 0]
    
    if not interventions_only.empty:
        # Get unique intervention types
        intervention_types = interventions_only['intervention_type'].unique()
        
        # Create a chart for each intervention type
        for intervention_type in intervention_types:
            if pd.notna(intervention_type):  # Skip NaN values
                st.markdown(f"**{intervention_type}**")
                
                # Filter for this specific intervention type
                type_data = interventions_only[
                    interventions_only['intervention_type'] == intervention_type
                ]
                
                # Group by date
                interventions_per_day = type_data.groupby('date').size().reset_index(name='count')
                interventions_per_day.columns = ['Date', 'Count']
                
                # Display bar chart
                st.bar_chart(interventions_per_day.set_index('Date'))
    else:
        st.info("No interventions recorded yet.")
    
    # Optional: Show raw data
    #with st.expander("See raw data"):
    #    st.dataframe(interactions)

def show():
    #--LOGIN GATE
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        st.warning("🚫 You must log in first.")
        st.stop()   # Prevents rest of the page from rendering
    
    with st.container(border=True):
        cols = st.columns(1, border=False)

        with cols[0]:
            if st.session_state["interventionalist"]:
                intervention_viz()
            else:
                infection_viz()
            
if __name__ == "__main__":
    show()


                
