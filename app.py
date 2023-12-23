from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_cors import CORS


app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin'
CORS(app)

# Простой словарь для логинов и паролей
users = {
    'admin': 'admin',
    'user1': 'password1'
}

# Конфигурация для баз
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_profiles.db'
app.config['SQLALCHEMY_BINDS'] = {
    'tournament_db': 'sqlite:///tournaments.db'
}

# Инициализация базы данных
db = SQLAlchemy(app)


# Создаем кастомный класс для представления главной страницы админ-панели
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if 'username' not in session:
            return redirect(url_for('login'))
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        session.pop('username', None)
        return redirect(url_for('login'))

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String(255))
    balance = db.Column(db.Integer, default=0)
    role = db.Column(db.String(255), default='user')

class Tournament(db.Model):
    __bind_key__ = 'tournament_db'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    teams = db.Column(db.String(255), nullable=False)
    teams_relation = db.relationship('Team', backref='tournament', lazy=True)

class Team(db.Model):
    __bind_key__ = 'tournament_db'
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    players_relation = db.relationship('Player', backref='team', lazy=True)

class Player(db.Model):
    __bind_key__ = 'tournament_db'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)

class Match(db.Model):
    __bind_key__ = 'tournament_db'
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    team1 = db.Column(db.String(255), nullable=False)
    team2 = db.Column(db.String(255), nullable=False)
    match_time = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    coefficient_win = db.Column(db.Float)  # Новые поля для коэффициентов
    coefficient_draw = db.Column(db.Float)
    coefficient_lose = db.Column(db.Float)

class Bet(db.Model):
    __bind_key__ = 'tournament_db'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    bet_type = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    coefficient = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(255), nullable=False)

# ModlesView
class TeamModelView(ModelView):
    form_columns = ('tournament_id', 'name')
    column_list = ['id', 'tournament_id', 'name']
    column_labels = {'tournament_id': 'Tournament ID'}

class PlayerModelView(ModelView):
    form_columns = ('team_id', 'name')
    column_list = ['id', 'team_id', 'name']
    column_labels = {'team_id': 'Team ID'}

class TournamentModelView(ModelView):
    column_list = ['id', 'name', 'teams']
    column_labels = {'name': 'Tournament Name', 'teams': 'Teams'}

class MatchModelView(ModelView):
    column_list = ['id', 'tournament_id', 'team1', 'team2', 'match_time', 'status', 'coefficient_win', 'coefficient_draw', 'coefficient_lose']
    form_columns = ('tournament_id', 'team1', 'team2', 'match_time', 'status', 'coefficient_win', 'coefficient_draw', 'coefficient_lose')

class BetModelView(ModelView):
    column_list = ['id', 'user_id', 'match_id', 'bet_type', 'amount', 'coefficient', 'status']
    form_columns = ('user_id', 'match_id', 'bet_type', 'amount', 'coefficient', 'status')


# Добавляем модели в админку
admin = Admin(app, name='Admin Panel', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_link(MenuLink(name='Logout', category='', url='/admin/logout/'))
admin.add_view(ModelView(User, db.session))
admin.add_view(TournamentModelView(Tournament, db.session))
admin.add_view(MatchModelView(Match, db.session))
admin.add_view(TeamModelView(Team, db.session))
admin.add_view(PlayerModelView(Player, db.session))
admin.add_view(BetModelView(Bet, db.session))


# Форма входа
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# Маршрут входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('admin.index'))
        else:
            return render_template('login.html', form=form, error="Invalid username or password")
    return render_template('login.html', form=form)

# Маршрут выхода
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Обработчик для админ-панели
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form_tournament = AddTournamentForm()
    form_team = AddTeamForm()
    form_player = AddPlayerForm()

    if form_tournament.validate_on_submit():
        name = form_tournament.name.data
        teams = form_tournament.teams.data
        coefficients = form_tournament.coefficients.data

        tournament = Tournament(name=name, teams=teams, coefficients=coefficients)
        db.session.add(tournament)
        db.session.commit()

    if form_team.validate_on_submit():
        tournament_id = form_team.tournament_id.data
        name = form_team.name.data

        team = Team(tournament_id=tournament_id, name=name)
        db.session.add(team)
        db.session.commit()

    if form_player.validate_on_submit():
        team_id = form_player.team_id.data
        name = form_player.name.data

        player = Player(team_id=team_id, name=name)
        db.session.add(player)
        db.session.commit()

    tournaments = Tournament.query.all()
    return render_template('admin.html', form_tournament=form_tournament, form_team=form_team, form_player=form_player, tournaments=tournaments)

# API
@app.route('/api/matches')
def get_matches():
    matches = Match.query.all()
    match_list = []
    for match in matches:
        match_info = {
            'id': match.id,
            'tournament_id': match.tournament_id,
            'team1': match.team1,
            'team2': match.team2,
            'match_time': match.match_time,
            'status': match.status,
            'coefficient_win': match.coefficient_win,
            'coefficient_draw': match.coefficient_draw,
            'coefficient_lose': match.coefficient_lose
        }
        match_list.append(match_info)
    return jsonify(match_list)

# Добавим функцию для создания всех таблиц в контексте Flask-приложения
def create_tables():
    with app.app_context():
        db.create_all()

# Если файл app.py запускается напрямую, создаем таблицы
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
