import streamlit as st
import pandas as pd
import json
from pathlib import Path

from scraper import scrape_world_cup_results


BASE_DIR = Path(__file__).resolve().parent

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
        with (BASE_DIR / 'predictions.json').open() as f:
            predictions = json.load(f)
        real_results = st.session_state.get("real_results")
        if real_results is None:
            with (BASE_DIR / 'real_results.json').open() as f:
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
            try:
                st.session_state["real_results"] = scrape_world_cup_results()
            except Exception as exc:
                st.error(f"Could not fetch latest results: {exc}")
            else:
                st.success("Latest results fetched.")
                st.rerun()

predictions, real_results = load_data()

if predictions and real_results:
    import altair as alt

    # Build dictionary of real scores
    real_scores = {}
    for r in real_results:
        if r.get('played'):
            real_scores[r['match_id']] = (r['scoreA'], r['scoreB'])
            
    # Get all players
    all_players = list(predictions[0]['predictions'].keys()) if predictions else []
    
    # Calculate player points
    player_points = {p: 0 for p in all_players}
    player_exact_scores = {p: 0 for p in all_players}
    player_match_details = {p: [] for p in all_players}
    match_player_details = {} 
    
    progression_data = []
    contrarian_bets = []
    
    for p_match in predictions:
        match_id = p_match['match_id']
        preds = p_match['predictions']
        match_label = f"{p_match['teamA']} vs {p_match['teamB']}"
        
        # Only process if the match has been played
        if match_id in real_scores:
            actual_a, actual_b = real_scores[match_id]
            real_score_str = f"{actual_a} - {actual_b}"
            
            # Count bets for Feature 9 (Most Common Bet)
            bet_counts = {}
            for player, p_scores in preds.items():
                p_str = f"{p_scores['teamA_score']} - {p_scores['teamB_score']}"
                bet_counts[p_str] = bet_counts.get(p_str, 0) + 1
            
            most_common_bet = max(bet_counts, key=bet_counts.get) if bet_counts else "None"
            pct_common = (bet_counts.get(most_common_bet, 0) / len(preds)) * 100 if preds else 0
            
            match_player_details[match_id] = {
                "label": match_label,
                "real_score": real_score_str,
                "most_common_bet": f"{most_common_bet} ({pct_common:.0f}%)",
                "bets": []
            }
            
            for player, p_scores in preds.items():
                p_a = p_scores['teamA_score']
                p_b = p_scores['teamB_score']
                predicted_str = f"{p_a} - {p_b}"
                
                points = calculate_points(p_a, p_b, actual_a, actual_b)
                player_points[player] += points
                
                if points == 3:
                    player_exact_scores[player] += 1
                    
                # Feature 4: Contrarian Award
                if points > 0:
                    popularity = bet_counts[predicted_str] / len(preds)
                    if popularity <= 0.15:
                        contrarian_bets.append({
                            "Player": player,
                            "Match": match_label,
                            "Predicted": predicted_str,
                            "Result": real_score_str,
                            "Points": points,
                            "Popularity": f"{popularity*100:.1f}%"
                        })
                
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
                
            # Feature 10: Point Progression
            for player in all_players:
                progression_data.append({
                    "Match ID": match_id,
                    "Match": match_label,
                    "Player": player,
                    "Cumulative Points": player_points[player]
                })

    # Sort players by total points
    sorted_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)
    player_names_sorted = [p[0] for p in sorted_players]

    # Top level tabs for better organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 Leaderboard", 
        "📈 Point Progression", 
        "📊 Player Details", 
        "⚔️ Head-to-Head", 
        "🧠 Deep Insights"
    ])
    
    with tab1:
        st.header("Overall Leaderboard")
        
        if sorted_players:
            df_leaderboard = pd.DataFrame(sorted_players, columns=['Player', 'Points'])
            df_leaderboard.index = df_leaderboard.index + 1
            
            st.subheader("Points Visualization")
            chart = alt.Chart(df_leaderboard).mark_bar(color='#1f77b4').encode(
                x=alt.X('Player:N', sort='-y', title='Player'),
                y=alt.Y('Points:Q', title='Points'),
                tooltip=['Player', 'Points']
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)
            
            col_l1, col_l2 = st.columns([2, 1])
            with col_l1:
                st.subheader("Leaderboard Table")
                st.dataframe(df_leaderboard, use_container_width=True)
                
            with col_l2:
                # Feature 7: Best Exact Score Sniper
                st.subheader("🎯 Exact Score Snipers")
                df_snipers = pd.DataFrame(list(player_exact_scores.items()), columns=["Player", "Exact Scores"])
                df_snipers = df_snipers.sort_values(by="Exact Scores", ascending=False).reset_index(drop=True)
                df_snipers.index = df_snipers.index + 1
                st.dataframe(df_snipers.head(10), use_container_width=True)
        else:
            st.info("No players found in predictions.")
            
    with tab2:
        # Feature 10: Point Progression Race
        st.header("Point Progression Race")
        if progression_data:
            df_prog = pd.DataFrame(progression_data)
            player_selection = alt.selection_point(
                fields=["Player"],
                bind="legend",
                toggle=True,
            )
            line_chart = alt.Chart(df_prog).mark_line(point=True).encode(
                x=alt.X('Match ID:O', title='Matches (Chronological)'),
                y=alt.Y('Cumulative Points:Q', title='Points'),
                color=alt.Color('Player:N', sort=player_names_sorted),
                opacity=alt.condition(player_selection, alt.value(1), alt.value(0.08)),
                tooltip=['Player', 'Match', 'Cumulative Points'],
            ).add_params(player_selection).properties(height=500)
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.info("No progression data available yet.")
            
    with tab3:
        st.header("Player Details")
        selected_player = st.selectbox("Select a player to see their bets and points:", player_names_sorted)
        if selected_player and player_match_details.get(selected_player):
            total_pts = player_points[selected_player]
            exact_scores = player_exact_scores[selected_player]
            
            # Show Metrics
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Total Points", total_pts)
            col_m2.metric("Exact Scores Predicted", exact_scores)
            
            st.divider()
            
            col_p1, col_p2 = st.columns([1, 1])
            with col_p1:
                st.subheader(f"{selected_player}'s Bets")
                df_player_bets = pd.DataFrame(player_match_details[selected_player])
                st.dataframe(df_player_bets, use_container_width=True)
                
            with col_p2:
                # Feature 2: Accuracy Breakdown Pie Chart
                st.subheader("Accuracy Breakdown")
                outcome_counts = df_player_bets['Outcome'].value_counts().reset_index()
                outcome_counts.columns = ['Outcome', 'Count']
                
                pie_chart = alt.Chart(outcome_counts).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Outcome", type="nominal", 
                        scale=alt.Scale(domain=['Exact Score', 'Exact Goal Diff', 'Right Winner', 'Wrong'],
                                        range=['#2ca02c', '#1f77b4', '#ff7f0e', '#d62728'])),
                    tooltip=['Outcome', 'Count']
                ).properties(height=350)
                st.altair_chart(pie_chart, use_container_width=True)
                
        elif selected_player:
            st.info("No played matches found for this player yet.")
            
    with tab4:
        # Feature 8: Head-to-Head Comparison
        st.header("Head-to-Head Comparison")
        if len(player_names_sorted) >= 2:
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                p1 = st.selectbox("Player 1", player_names_sorted, index=0)
            with col_h2:
                p2 = st.selectbox("Player 2", player_names_sorted, index=1)
                
            if p1 and p2 and p1 != p2:
                p1_bets = {d["Match"]: d for d in player_match_details[p1]}
                p2_bets = {d["Match"]: d for d in player_match_details[p2]}
                
                h2h_data = []
                for match in p1_bets.keys():
                    if match in p2_bets:
                        b1 = p1_bets[match]
                        b2 = p2_bets[match]
                        h2h_data.append({
                            "Match": match,
                            "Real Result": b1["Real Score"],
                            f"{p1} Bet": b1["Predicted"],
                            f"{p1} Pts": b1["Points"],
                            f"{p2} Bet": b2["Predicted"],
                            f"{p2} Pts": b2["Points"],
                        })
                
                if h2h_data:
                    df_h2h = pd.DataFrame(h2h_data)
                    st.dataframe(df_h2h, use_container_width=True)
                    
                    # Quick H2H Summary
                    p1_h2h_pts = df_h2h[f"{p1} Pts"].sum()
                    p2_h2h_pts = df_h2h[f"{p2} Pts"].sum()
                    st.write(f"**Head-to-Head Points (Played Matches):** {p1} ({p1_h2h_pts}) vs {p2} ({p2_h2h_pts})")
                else:
                    st.info("No overlapping played matches found.")
            elif p1 == p2:
                st.warning("Please select two different players.")
                
    with tab5:
        st.header("Deep Insights")
        
        # Feature 4: The Contrarian Award
        st.subheader("🦄 The Contrarian Award")
        st.write("Players who scored points on an outcome that less than 15% of the group predicted!")
        if contrarian_bets:
            df_contra = pd.DataFrame(contrarian_bets)
            df_contra = df_contra.sort_values(by="Points", ascending=False).reset_index(drop=True)
            st.dataframe(df_contra, use_container_width=True)
        else:
            st.info("No contrarian bets have scored points yet.")
            
        st.divider()
        
        # Feature 9: Most Common Bet vs Reality (Integrated into expanders)
        st.subheader("Latest Match Results: Crowd vs Reality")
        st.write("Expand a match to see the crowd's most popular bet vs what actually happened.")
        
        if match_player_details:
            for m_id, m_data in match_player_details.items():
                with st.expander(f"{m_data['label']} | Result: {m_data['real_score']}"):
                    st.markdown(f"**Actual Result:** {m_data['real_score']}")
                    st.markdown(f"**Crowd's Most Common Bet:** {m_data['most_common_bet']}")
                    
                    df_match_bets = pd.DataFrame(m_data["bets"])
                    df_match_bets = df_match_bets.sort_values(by="Points", ascending=False).reset_index(drop=True)
                    st.dataframe(df_match_bets, use_container_width=True)
        else:
            st.info("No matches have finished yet.")
