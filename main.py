import sqlalchemy.orm.query
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from ast import literal_eval


API_KEY = os.environ.get('API_KEY')
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(250), unique=True, nullable=False)
    rating = db.Column(db.Integer, unique=False, nullable=True)
    ranking = db.Column(db.Integer, unique=True, nullable=True)
    review = db.Column(db.String(1000), unique=True, nullable=True)
    img_url = db.Column(db.String(1000), unique=True, nullable=False)


class RatingForm(FlaskForm):
    rating = StringField('Rating', validators=[DataRequired()])
    review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class NewMovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


db.create_all()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = NewMovieForm()

    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(MOVIE_DB_SEARCH_URL, params = {
            'api_key': API_KEY,
            'query': movie_title
        })
        data = response.json()['results']
        return render_template('select.html', options=data)

    return render_template("add.html", form=form)


@app.route("/edit", methods=['GET', 'POST'])
def rate():
    form = RatingForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/find")
def find():
    movie_api_id = request.args.get('id')
    if movie_api_id:
        movie_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_url, params={'api_key': API_KEY})
        data = response.json()

        new_movie = Movie(
            title=data["title"],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            year=data['release_date'].split("-")[0],
            description=data['overview']
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('rate', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
