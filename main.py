from dotenv import load_dotenv

load_dotenv()
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
import sqlalchemy_utils

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['MY_SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)
MOVIE_DATABASE_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_API_KEY = os.environ["MOVIE_DB_API_KEY"]


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


if not sqlalchemy_utils.functions.database_exists('sqlite:///my_movies.db'):
    db.create_all()


class MovieForm(FlaskForm):
    movie_title = StringField('Movie Name', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


class EditForm(FlaskForm):
    movie_rating = FloatField('Your rating out of 10, e.g. 7.5', validators=[DataRequired()])
    movie_review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=['POST', 'GET'])
def add():
    form = MovieForm()
    if form.validate_on_submit():
        movie_title = form.movie_title.data
        search_params = {"api_key": MOVIE_DB_API_KEY, "query": movie_title}
        response = requests.get(url=MOVIE_DATABASE_URL, params=search_params)
        data = response.json()["results"]
        print(data)
        return render_template("select.html", search_options=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get('id')
    if movie_id:
        movie_params = {"api_key": MOVIE_DB_API_KEY, "movie_id": movie_id}
        movie_response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_id}", params=movie_params)
        requested_movie = movie_response.json()
        print(requested_movie)
        new_movie = Movie(title=requested_movie["title"],year=requested_movie["release_date"].split("-")[0],
                          description=requested_movie["overview"],
                          img_url=f"https://image.tmdb.org/t/p/w500{requested_movie['poster_path']}")
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit_movie', id=new_movie.id))


@app.route("/edit", methods=['POST', 'GET'])
def edit_movie():
    form = EditForm()
    requested_movie_id = request.args.get("id")
    requested_movie = Movie.query.get(requested_movie_id)
    if form.validate_on_submit():
        requested_movie.rating = form.movie_rating.data
        requested_movie.review = form.movie_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=requested_movie)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
