import streamlit as st
import pandas as pd
import json
import subprocess

def calculate_points(predicted_a, predicted_b, actual_a, actual_b):
    if predicted_a == actual_a and predicted_b == actual_b:
        return 3
    
    predicted_diff = predicted_a - predicted_b
    actual_diff = actual_a - actual_b
    if predicted_diff == actual_diff:
        return 2
        
    predicted_outcome = 1 if predicted_a > predicted_b else (-1 if predicted_a < predicted_b else 0)
    actual_outcome = 1 if actual_a > actual_b else (-1 if actual_a < actual_b else 0)
    
    if predicted_outcome == actual_outcome:
        return 1
        
    return 0

def load_data():
    try:
        with open('predictions.json', 'r') as f:
            predictions = json.load(f)
        with open('real_results.json', 'r') as f:
            real_results = json.load(f)
        return predictions, real_results
    except FileNotFoundError:
        st.error("Could not find predictions.json or real_results.json. Make sure to run scraper.py first.")
        return None, None

st.set_page_config(layout="wide")
st.title("🏆 World Cup 2026 Betting Dashboard")

col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🔄 Fetch Latest Results"):
        with st.spinner("Scraping Wikipedia for latest results..."):
            subprocess.run(["python3", "scraper.py"])
            st.rerun()

predictions, real_results = load_data()

if predictions and real_results:
    # Build dictionary of real scores
    real_scores = {}
    for r in real_results:
        if r.get('played'):
            real_scores[r['match_id']] = (r['scoreA'], r['scoreB'])
            
    # Calculate player points
    player_points = {}
    player_match_details = {} 
    match_player_details = {} 
    
    # Pre-initialize dictionaries
    for p_match in predictions:
        for player in p_match['predictions'].keys():
            if player not in player_points:
                player_points[player] = 0
            if player not in player_match_details:
                player_match_details[player] = []
                
    for p_match in predictions:
        match_id = p_match['match_id']
        preds = p_match['predictions']
        match_label = f"{p_match['teamA']} vs {p_match['teamB']}"
        
        # Only add points if the match has been played
        if match_id in real_scores:
            actual_a, actual_b = real_scores[match_id]
            real_score_str = f"{actual_a} - {actual_b}"
            
            match_player_details[match_id] = {
                "label": match_label,
                "real_score": real_score_str,
                "bets": []
            }
            
            for player, p_scores in preds.items():
                p_a = p_scores['teamA_score']
                p_b = p_scores['teamB_score']
                predicted_str = f"{p_a} - {p_b}"
                
                points = calculate_points(p_a, p_b, actual_a, actual_b)
                player_points[player] += points
                
                # Determine outcome type for nicer visuals
                outcome_type = "Wrong"
                if points == 3: outcome_type = "Exact Score"
                elif points == 2: outcome_type = "Exact Goal Diff"
                elif points == 1: outcome_type = "Right Winner"
                
                player_match_details[player].append({
                    "Match": match_label,
                    "Real Score": real_score_str,
                    "Predicted": predicted_str,
                    "Points": points,
                    "Outcome": outcome_type
                })
                
                match_player_details[match_id]["bets"].append({
                    "Player": player,
                    "Predicted": predicted_str,
                    "Points": points
                })

    # Top level tabs for better organization
    tab1, tab2 = st.tabs(["🏆 Leaderboard", "📊 Player & Match Details"])
    
    with tab1:
        st.header("Overall Leaderboard")
        sorted_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_players:
            df_leaderboard = pd.DataFrame(sorted_players, columns=['Player', 'Points'])
            df_leaderboard.index = df_leaderboard.index + 1
            
            # Display nicer Visualization (Bar Chart)
            import altair as alt
            st.subheader("Points Visualization")
            
            # Use Altair to guarantee sorting by Points (highest first)
            chart = alt.Chart(df_leaderboard).mark_bar(color='#1f77b4').encode(
                x=alt.X('Player:N', sort='-y', title='Player'),
                y=alt.Y('Points:Q', title='Points'),
                tooltip=['Player', 'Points']
            ).properties(height=350)
            
            st.altair_chart(chart, use_container_width=True)
            
            # Display Table
            st.subheader("Leaderboard Table")
            st.dataframe(df_leaderboard, use_container_width=True)
        else:
            st.info("No players found in predictions.")
            
    with tab2:
        st.header("Player Details")
        selected_player = st.selectbox("Select a player to see their bets and points:", [p for p, _ in sorted_players])
        if selected_player and player_match_details.get(selected_player):
            total_pts = player_points[selected_player]
            exact_scores = sum(1 for b in player_match_details[selected_player] if b["Points"] == 3)
            
            # Show Metrics
            col1, col2 = st.columns(2)
            col1.metric("Total Points", total_pts)
            col2.metric("Exact Scores Predicted", exact_scores)
            
            st.subheader(f"{selected_player}'s Bets")
            df_player_bets = pd.DataFrame(player_match_details[selected_player])
            
            # Use dataframe with color styling for points
            st.dataframe(df_player_bets, use_container_width=True)
        elif selected_player:
            st.info("No played matches found for this player yet.")
            
        st.divider()

        st.header("Latest Match Results")
        st.write("Expand a match to see what everybody bet and how many points they got.")
        
        if match_player_details:
            for m_id, m_data in match_player_details.items():
                with st.expander(f"{m_data['label']} | Result: {m_data['real_score']}"):
                    df_match_bets = pd.DataFrame(m_data["bets"])
                    df_match_bets = df_match_bets.sort_values(by="Points", ascending=False).reset_index(drop=True)
                    st.dataframe(df_match_bets, use_container_width=True)
        else:
            st.info("No matches have finished yet.")
