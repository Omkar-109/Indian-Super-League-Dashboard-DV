from flask import Flask, render_template_string
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Flask(__name__)

@app.route('/')
def index():
    # ==================== LOAD DATA ====================
    df = pd.read_csv('data/isl_matches.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Year']
    df['month_name'] = df['Date'].dt.strftime('%B')
    df['day_of_week'] = df['Day']
    
    # ==================== CHART 1: Goals Trend Over Time ====================
    trend_data = df.groupby('Date')['total_goals'].mean().reset_index()
    fig1 = px.line(trend_data, x='Date', y='total_goals',
                   title='⚽ Goals Trend Over All Seasons',
                   labels={'total_goals': 'Average Goals', 'Date': 'Match Date'})
    fig1.update_traces(line_color='#7eb0d5', line_width=3)
    fig1.update_layout(template='plotly_white', hovermode='x unified')
    
    # ==================== CHART 2: Home vs Away Wins ====================
    home_wins = len(df[df['winner'] == df['Home']])
    away_wins = len(df[df['winner'] == df['Away']])
    draws = len(df) - home_wins - away_wins
    
    fig2 = px.pie(values=[home_wins, away_wins, draws],
                  names=['Home Wins', 'Away Wins', 'Draws'],
                  title='🏠 Home vs Away Wins Distribution',
                  color_discrete_sequence=['#b2e061', '#fd7f6f', '#beb9db'],
                  hole=0.4)
    fig2.update_layout(template='plotly_white')
    
    # ==================== CHART 3: Goal Distribution ====================
    goal_bins = [0, 1, 2, 3, 4, 10]
    goal_labels = ['0-1', '2', '3', '4', '5+']
    df['goal_range'] = pd.cut(df['total_goals'], bins=goal_bins, labels=goal_labels)
    goal_dist = df['goal_range'].value_counts().sort_index().reset_index()
    goal_dist.columns = ['Goals', 'Frequency']
    
    fig3 = px.bar(goal_dist, x='Goals', y='Frequency',
                  title='🎯 Goal Distribution Across All Matches',
                  color='Goals',
                  color_discrete_sequence=['#7eb0d5', '#fd7f6f', '#b2e061', '#bd7ebe', '#ffb55a'])
    fig3.update_layout(template='plotly_white', showlegend=False)
    
    # ==================== CHART 4: Performance by Day of Week ====================
    day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_stats = df.groupby('Day').agg({
        'total_goals': 'mean',
        'Date': 'count'
    }).reset_index()
    day_stats['Day'] = pd.Categorical(day_stats['Day'], categories=day_order, ordered=True)
    day_stats = day_stats.sort_values('Day')
    
    fig4 = px.bar(day_stats, x='Day', y='total_goals',
                  title='📅 Average Goals by Day of Week',
                  labels={'total_goals': 'Average Goals', 'Day': 'Day of Week'},
                  text='total_goals')
    fig4.update_traces(marker_color='#ffb55a', texttemplate='%{text:.2f}', textposition='outside')
    fig4.update_layout(template='plotly_white')
    
    # ==================== CHART 5: Top 10 Venues by Average Goals ====================
    venue_stats = df.groupby('Venue').agg({
        'total_goals': 'mean',
        'Date': 'count'
    }).rename(columns={'Date': 'Matches'}).reset_index()
    top_venues = venue_stats.nlargest(10, 'total_goals')
    
    fig5 = px.bar(top_venues, x='total_goals', y='Venue', orientation='h',
                  title='🏟️ Top 10 Venues by Average Goals',
                  labels={'total_goals': 'Average Goals'},
                  color='total_goals',
                  color_continuous_scale='Viridis')
    fig5.update_layout(template='plotly_white', showlegend=False)
    
    # ==================== CHART 6: Scoring Patterns Heatmap ====================
    score_matrix = df.groupby(['home_team_score', 'away_team_score']).size().reset_index(name='count')
    pivot_scores = score_matrix.pivot(index='away_team_score', columns='home_team_score', values='count').fillna(0)
    
    fig6 = px.imshow(pivot_scores,
                     title='📊 Scoring Patterns (Home vs Away Score Frequency)',
                     labels=dict(x="Home Team Score", y="Away Team Score", color="Matches"),
                     color_continuous_scale='RdYlBu_r',
                     aspect='auto')
    fig6.update_layout(template='plotly_white')
    
    # ==================== CHART 7: Goals by Year ====================
    yearly_stats = df.groupby('Year').agg({
        'total_goals': 'mean',
        'Date': 'count'
    }).rename(columns={'Date': 'Matches'}).reset_index()
    
    fig7 = make_subplots(specs=[[{"secondary_y": True}]])
    fig7.add_trace(
        go.Bar(x=yearly_stats['Year'], y=yearly_stats['Matches'],
               name="Matches Played", marker_color='#b2e061', opacity=0.6),
        secondary_y=False
    )
    fig7.add_trace(
        go.Scatter(x=yearly_stats['Year'], y=yearly_stats['total_goals'],
                   name="Avg Goals", line=dict(color='#7eb0d5', width=4),
                   mode='lines+markers'),
        secondary_y=True
    )
    fig7.update_layout(
        title='📈 Yearly Trends: Matches and Average Goals',
        template='plotly_white',
        hovermode='x unified'
    )
    fig7.update_yaxes(title_text="Number of Matches", secondary_y=False)
    fig7.update_yaxes(title_text="Average Goals per Match", secondary_y=True)
    
    # ==================== CHART 8: Team Performance ====================
    teams = sorted(set(df['Home'].unique()) | set(df['Away'].unique()))
    team_stats = []
    
    for team in teams:
        home_matches = df[df['Home'] == team]
        away_matches = df[df['Away'] == team]
        
        total_matches = len(home_matches) + len(away_matches)
        wins = len(df[df['winner'] == team])
        home_goals = home_matches['home_team_score'].sum()
        away_goals = away_matches['away_team_score'].sum()
        
        team_stats.append({
            'Team': team,
            'Matches': total_matches,
            'Wins': wins,
            'Goals': int(home_goals + away_goals),
            'Win Rate': round((wins/total_matches)*100, 1) if total_matches > 0 else 0
        })
    
    team_df = pd.DataFrame(team_stats).sort_values('Win Rate', ascending=False).head(10)
    
    fig8 = px.bar(team_df, x='Win Rate', y='Team', orientation='h',
                  title='🏆 Top 10 Teams by Win Rate (%)',
                  color='Win Rate',
                  color_continuous_scale='RdYlGn',
                  text='Win Rate')
    fig8.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig8.update_layout(template='plotly_white', showlegend=False)
    
    # ==================== CHART 9: Attendance Analysis ====================
    attendance_by_year = df.groupby('Year')['Attendance'].mean().reset_index()
    
    fig9 = px.line(attendance_by_year, x='Year', y='Attendance',
                   title='👥 Average Attendance by Year',
                   markers=True,
                   labels={'Attendance': 'Average Attendance'})
    fig9.update_traces(line_color='#bd7ebe', line_width=3, marker_size=10)
    fig9.update_layout(template='plotly_white')
    
    # ==================== Generate HTML for all charts ====================
    graph_html1 = fig1.to_html(full_html=False)
    graph_html2 = fig2.to_html(full_html=False)
    graph_html3 = fig3.to_html(full_html=False)
    graph_html4 = fig4.to_html(full_html=False)
    graph_html5 = fig5.to_html(full_html=False)
    graph_html6 = fig6.to_html(full_html=False)
    graph_html7 = fig7.to_html(full_html=False)
    graph_html8 = fig8.to_html(full_html=False)
    graph_html9 = fig9.to_html(full_html=False)
    
    # ==================== Dashboard HTML Template ====================
    html = '''
    <!DOCTYPE html>
    <html>
        <head>
            <title>ISL Analytics Dashboard</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 20px;
                    min-height: 100vh;
                }
                
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px;
                    border-radius: 15px;
                    text-align: center;
                    margin-bottom: 30px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                }
                
                .header h1 {
                    color: white;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    font-weight: 700;
                }
                
                .header p {
                    color: #f0f0f0;
                    font-size: 1.2em;
                    font-weight: 300;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                
                .stat-card {
                    background: white;
                    padding: 25px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                    transition: transform 0.3s ease;
                }
                
                .stat-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                }
                
                .stat-number {
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #667eea;
                    margin-bottom: 10px;
                }
                
                .stat-label {
                    color: #666;
                    font-size: 0.95em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .chart-grid {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 30px;
                }
                
                .chart-row-2 {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                    gap: 30px;
                }
                
                .chart {
                    background: white;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                    padding: 20px;
                    border-radius: 12px;
                    transition: box-shadow 0.3s ease;
                }
                
                .chart:hover {
                    box-shadow: 0 6px 25px rgba(0,0,0,0.12);
                }
                
                .footer {
                    text-align: center;
                    margin-top: 50px;
                    padding: 20px;
                    color: #666;
                    font-size: 0.9em;
                }
                
                @media (max-width: 768px) {
                    .header h1 {
                        font-size: 1.8em;
                    }
                    
                    .chart-row-2 {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚽ Indian Super League</h1>
                    <p>Comprehensive Analytics Dashboard</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">1,056</div>
                        <div class="stat-label">Total Matches</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">2.8</div>
                        <div class="stat-label">Avg Goals/Match</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">10,353</div>
                        <div class="stat-label">Avg Attendance</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">9 Years</div>
                        <div class="stat-label">2014-2023</div>
                    </div>
                </div>
                
                <div class="chart-grid">
                    <div class="chart">
                        {{ graph_html1|safe }}
                    </div>
                    
                    <div class="chart-row-2">
                        <div class="chart">
                            {{ graph_html2|safe }}
                        </div>
                        <div class="chart">
                            {{ graph_html3|safe }}
                        </div>
                    </div>
                    
                    <div class="chart-row-2">
                        <div class="chart">
                            {{ graph_html4|safe }}
                        </div>
                        <div class="chart">
                            {{ graph_html9|safe }}
                        </div>
                    </div>
                    
                    <div class="chart">
                        {{ graph_html7|safe }}
                    </div>
                    
                    <div class="chart-row-2">
                        <div class="chart">
                            {{ graph_html5|safe }}
                        </div>
                        <div class="chart">
                            {{ graph_html8|safe }}
                        </div>
                    </div>
                    
                    <div class="chart">
                        {{ graph_html6|safe }}
                    </div>
                </div>
                
                <div class="footer">
                    <p>© 2025 Indian Super League Analytics Dashboard</p>
                    <p>Data from ISL Matches 2014-2023 | Built with Flask & Plotly</p>
                </div>
            </div>
        </body>
    </html>
    '''
    
    return render_template_string(html, 
                                 graph_html1=graph_html1,
                                 graph_html2=graph_html2,
                                 graph_html3=graph_html3,
                                 graph_html4=graph_html4,
                                 graph_html5=graph_html5,
                                 graph_html6=graph_html6,
                                 graph_html7=graph_html7,
                                 graph_html8=graph_html8,
                                 graph_html9=graph_html9)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
