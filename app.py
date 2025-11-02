from flask import Flask, render_template
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

    # =================== TEXT BASED OUTPUTS ==================================

    # =================== 1 : Total maches across all seasons
    all_season_total_matches = len(df)

    # =================== 2 : Total Seasons ==================================
    total_seasons = df['Year'].nunique()


    # ====================== CHARTS ===========================================
    
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
     
    
    # ==================== CHART 5: Attendance Analysis ====================
    attendance_by_year = df.groupby('Year')['Attendance'].mean().reset_index()
    
    fig5 = px.line(attendance_by_year, x='Year', y='Attendance',
                   title='👥 Average Attendance by Year',
                   markers=True,
                   labels={'Attendance': 'Average Attendance'})
    fig5.update_traces(line_color='#bd7ebe', line_width=3, marker_size=10)
    fig5.update_layout(template='plotly_white')
    
    # ==================== Generate HTML for all charts ====================
    graph_html1 = fig1.to_html(full_html=False)
    graph_html2 = fig2.to_html(full_html=False)
    graph_html3 = fig3.to_html(full_html=False)
    graph_html4 = fig4.to_html(full_html=False)
    graph_html5 = fig5.to_html(full_html=False)
    
    
    
    return render_template('index.html',
                                  all_season_total_matches=all_season_total_matches,
                                  total_seasons=total_seasons, 
                                 graph_html1=graph_html1,
                                 graph_html2=graph_html2,
                                 graph_html3=graph_html3,
                                 graph_html4=graph_html4,
                                 graph_html5=graph_html5)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
