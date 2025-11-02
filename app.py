from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Flask(__name__)

# home as well as matches stat dashboard
@app.route('/')
def index():
    # ==================== LOAD DATA ====================
    df = pd.read_csv('data/Transformed_isl_matches_dataset.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['month_name'] = df['Date'].dt.strftime('%B')
    df['day_of_week'] = df['Day']

    # =================== TEXT BASED OUTPUTS ==================================
    all_season_total_matches = len(df)
    total_seasons = df['Year'].nunique()
    total_goals = df['total_goals'].sum()
    avg_attendance = int(df['Attendance'].mean())

    # Most successful team (by total wins, excluding draws)
    team_wins = df[df['winner'].notna() & (df['winner'].str.lower() != 'draw')]['winner'].value_counts().reset_index()
    team_wins.columns = ['Team', 'Wins']
    most_successful_team = team_wins.iloc[0]['Team'] if not team_wins.empty else "N/A"

    # Average Goals per Match
    avg_goals_per_match = round(df['total_goals'].mean(), 2)

    # Total Attendance (sum of all matches)
    total_attendance = int(df['Attendance'].sum())
    
    # Most successful team (by total wins, excluding draws)
    team_wins = df[df['winner'].notna() & (df['winner'].str.lower() != 'draw')]['winner'].value_counts().reset_index()
    team_wins.columns = ['Team', 'Wins']
    most_successful_team = team_wins.iloc[0]['Team'] if not team_wins.empty else "N/A"

    # League Leaderboard (Top 5 Teams)
    leaderboard = team_wins.head(5).to_dict(orient='records')



    # ====================== CHARTS ===========================================

    # Chart 1: Goals Trend Over Time
    trend_data = df.groupby('Date')['total_goals'].sum().reset_index()
    fig1 = px.line(trend_data, x='Date', y='total_goals',
                   title='⚽ Total Goals Scored Over Time',
                   labels={'total_goals': 'Total Goals', 'Date': 'Match Date'})
    fig1.update_traces(line_color='#7eb0d5', line_width=3)
    fig1.update_layout(template='plotly_white', hovermode='x unified')

    # Chart 2: Home vs Away Wins Distribution
    home_wins = len(df[df['winner'] == df['Home']])
    away_wins = len(df[df['winner'] == df['Away']])
    draws = len(df[df['winner'].isna()])

    fig2 = px.pie(values=[home_wins, away_wins, draws],
                  names=['Home Wins', 'Away Wins', 'Draws'],
                  title='🏠 Home vs Away Wins Distribution',
                  color_discrete_sequence=['#b2e061', '#fd7f6f', '#beb9db'],
                  hole=0.4)
    fig2.update_layout(template='plotly_white')

    # Chart 3: Goal Distribution
    goal_bins = [0, 1, 2, 3, 4, 10]
    goal_labels = ['0-1', '2', '3', '4', '5+']
    df['goal_range'] = pd.cut(df['total_goals'], bins=goal_bins, labels=goal_labels)
    goal_dist = df['goal_range'].value_counts().sort_index().reset_index()
    goal_dist.columns = ['Goals', 'Frequency']

    fig3 = px.bar(goal_dist, x='Goals', y='Frequency',
                  title='🎯 Goal Distribution per Match',
                  color='Goals',
                  color_discrete_sequence=['#7eb0d5', '#fd7f6f', '#b2e061', '#bd7ebe', '#ffb55a'])
    fig3.update_layout(template='plotly_white', showlegend=False)

    # Chart 4: Average Goals by Day of Week
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_stats = df.groupby('Day')['total_goals'].mean().reset_index()
    day_stats['Day'] = pd.Categorical(day_stats['Day'], categories=day_order, ordered=True)
    day_stats = day_stats.sort_values('Day')

    fig4 = px.bar(day_stats, x='Day', y='total_goals',
                  title='📅 Average Goals by Day of the Week',
                  labels={'total_goals': 'Average Goals', 'Day': 'Day'},
                  text='total_goals')
    fig4.update_traces(marker_color='#ffb55a', texttemplate='%{text:.2f}', textposition='outside')
    fig4.update_layout(template='plotly_white')

    # Chart 5: Average Attendance by Year
    attendance_by_year = df.groupby('Year')['Attendance'].mean().reset_index()
    fig5 = px.line(attendance_by_year, x='Year', y='Attendance',
                   title='👥 Average Attendance per Year',
                   markers=True,
                   labels={'Attendance': 'Average Attendance'})
    fig5.update_traces(line_color='#bd7ebe', line_width=3, marker_size=10)
    fig5.update_layout(template='plotly_white')

    # Chart 6: Top Venues by Attendance
    top_venues = df.groupby('Venue')['Attendance'].mean().reset_index().sort_values(by='Attendance', ascending=False).head(5)
    fig6 = px.bar(top_venues, x='Venue', y='Attendance',
                  title='🏟️ Top 5 Venues by Average Attendance',
                  text='Attendance',
                  color='Venue',
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig6.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig6.update_layout(template='plotly_white', showlegend=False)
    

    # Chart 7: Monthly Goal Trend
    monthly_goals = df.groupby('month_name')['total_goals'].sum().reindex([
        'January','February','March','April','May','June','July','August','September','October','November','December'
    ]).dropna().reset_index()

    fig7 = px.bar(monthly_goals, x='month_name', y='total_goals',
                title='📈 Total Goals by Month (Seasonal Trend)',
                color='total_goals',
                color_continuous_scale='Agsunset')
    fig7.update_layout(template='plotly_white', xaxis_title='Month', yaxis_title='Total Goals')

    


    # ==================== Generate HTML for all charts ====================
    graphs = [fig.to_html(full_html=False) for fig in [fig1, fig2, fig3, fig4, fig5, fig6, fig7]]

    # ==================== Render to Template ====================
    return render_template(
        'index.html',
        all_season_total_matches=all_season_total_matches,
        total_seasons=total_seasons,
        total_goals=total_goals,
        avg_attendance=avg_attendance,
        avg_goals_per_match=avg_goals_per_match,
        total_attendance=total_attendance,
        most_successful_team=most_successful_team,
        leaderboard=leaderboard,
        graphs=graphs
    )


# player stat dashboard
@app.route('/playerStat')
def player_stat():

    # ==================== LOAD DATA ====================
    df_players = pd.read_csv('data/transformed_isl_player24_25_dataset.csv')
    # Clean column names
    df_players.columns = df_players.columns.str.strip().str.replace('\xa0', ' ').str.replace(' ', '_')

    # =================== TEXT BASED OUTPUTS ==================================
    total_goals = df_players["Goals"].sum()
    total_assists = df_players["Assists"].sum()
    total_yellow_cards = df_players["Yellow_Cards"].sum()
    total_red_cards = df_players["Red_Cards"].sum()

    # ====================== CHARTS ===========================================

    # ============== Top 10 scorers ===========================
    top_goals = df_players.sort_values("Goals", ascending=False).head(10)
    p_fig1 = px.bar(top_goals, x="Player", y="Goals", color="Squad",
              title="Top 10 Goal Scorers", text="Goals")
    p_fig1.update_traces(textposition='outside')
    p_fig1.update_layout(template='plotly_white')

    # ============= Top 5 assist providers =================
    top_assists = df_players.sort_values("Assists", ascending=False).head(5)
    p_fig2 = px.bar(top_assists, x="Player", y="Assists", color="Squad",
              title="Top 5 Assist Providers", text="Assists")
    p_fig2.update_traces(textposition='outside')
    p_fig2.update_layout(template='plotly_white')
    
    # ============ Top 5 Players by Appearances ====================
    top_appearances = df_players.sort_values("Matches_Played", ascending=False).head(5)
    p_fig3 = px.bar(top_appearances, x="Player", y="Matches_Played", color="Squad",
              title="Top 5 Players by Appearances", text="Matches_Played")
    p_fig3.update_traces(textposition='outside')
    p_fig3.update_layout(template='plotly_white')

    # ============== Top 5 Players by Starts ========================
    top_starts = df_players.sort_values("Starts", ascending=False).head(5)
    p_fig4 = px.bar(top_starts, x="Player", y="Starts", color="Squad",
              title="Top 5 Players by Starts", text="Starts")
    p_fig4.update_traces(textposition='outside')
    p_fig4.update_layout(template='plotly_white')

    # =============== Average Age of Players by Club =================
    avg_age_club = df_players.groupby("Squad")["Age"].mean().reset_index()
    p_fig5 = px.bar(avg_age_club, x="Age", y="Squad",orientation='h', color="Squad",
              title="Average Age of Players by Club", text="Age")
    p_fig5.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    p_fig5.update_layout(xaxis={'categoryorder':'total descending'})
    p_fig5.update_layout(template='plotly_white')


    # ============================ Top 5 Clubs by Total Goals ================
    club_goals = df_players.groupby("Squad")["Goals"].sum().reset_index()
    top5_clubs_goals = club_goals.sort_values("Goals", ascending=False).head(5)
    p_fig6 = px.bar(top5_clubs_goals, x="Squad", y="Goals", color="Squad",
              title="Top 5 Clubs by Total Goals", text="Goals")
    p_fig6.update_traces(textposition='outside')
    p_fig6.update_layout(template='plotly_white')

    # ======================= India vs Foreign Players ========================
    # Extract nationality info — 'inIND' for Indian, others for foreign
    df_players['Player_Type'] = df_players['Nation'].apply(lambda x: 'Indian' if 'in' in x.lower() else 'Foreign')

    player_counts = df_players['Player_Type'].value_counts().reset_index()
    player_counts.columns = ['Type', 'Count']

    p_fig7 = px.pie(player_counts, names='Type', values='Count',
              color='Type', title="Indian vs Foreign Players Distribution",
              color_discrete_map={'Indian':'#008000', 'Foreign':'#FF6347'})
    p_fig7.update_layout(template='plotly_white')







    # ==================== Generate HTML for all charts ====================
    p_graph_html1 = p_fig1.to_html(full_html=False)
    p_graph_html2 = p_fig2.to_html(full_html=False)
    p_graph_html3 = p_fig3.to_html(full_html=False)
    p_graph_html4 = p_fig4.to_html(full_html=False)
    p_graph_html5 = p_fig5.to_html(full_html=False)
    p_graph_html6 = p_fig6.to_html(full_html=False)
    p_graph_html7 = p_fig7.to_html(full_html=False)








    return render_template('playerStat.html',
                           total_goals=total_goals,
                           total_assists=total_assists,
                           total_yellow_cards=total_yellow_cards,
                           total_red_cards=total_red_cards,
                           
                           p_graph_html1=p_graph_html1,
                           p_graph_html2=p_graph_html2,
                           p_graph_html3=p_graph_html3,
                           p_graph_html4=p_graph_html4,
                           p_graph_html5=p_graph_html5,
                           p_graph_html6=p_graph_html6,
                           p_graph_html7=p_graph_html7
                           )
                           
                           
                           

if __name__ == '__main__':
    app.run(debug=True, port=5000)
