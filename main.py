from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, FloatField, StringField
from wtforms.validators import DataRequired, NumberRange
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# Create DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"
db = SQLAlchemy()
db.init_app(app)


# Create Table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True)
    year = db.Column(db.Integer)
    description = db.Column(db.String)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String)
    img_url = db.Column(db.String)


with app.app_context():
    db.create_all()


# API TMDB
bearer = os.environ['API_READ']
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {bearer}"
}


# WTForm Update
class UpdateForm(FlaskForm):
    rating = FloatField("Your Rating out of 10 e.g. 7.5: ", validators=[DataRequired(),
                                                                        NumberRange(1, 10, message="Between 1 -10")])
    review = StringField("Your Review: ", validators=[DataRequired()])
    submit = SubmitField()


class AddForm(FlaskForm):
    title = StringField("Movie Title: ", validators=[DataRequired()])
    submit = SubmitField()


@app.route("/")
def home():
    movies_collection = db.session.execute(db.select(Movie).order_by(Movie.rating.desc())).scalars().all()
    rank = 1
    for movie in movies_collection:
        movie.ranking = rank
        rank += 1
    db.session.commit()
    return render_template("index.html", movies=movies_collection)


@app.route("/edit", methods=['POST', 'GET'])
def edit():
    movie_id = request.args.get("id")
    # Get data-row
    movie = db.get_or_404(Movie, movie_id)
    update_form = UpdateForm()
    if update_form.validate_on_submit():
        # Update Movie entry
        movie.rating = update_form.rating.data
        movie.review = update_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=update_form, movie=movie)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():

        url = "https://api.themoviedb.org/3/search/movie?query=armageddon"
        payload = {'query': add_form.title.data}
        response = requests.get(url, params=payload, headers=headers)
        movies = response.json()["results"]

        return render_template('select.html', movies=movies)

    return render_template('add.html', form=add_form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")

    # API themoviedb.org
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url, headers=headers).json()
    new_movie = Movie(
        title=response["title"],
        year=response["release_date"].split("-")[0],
        description=response["overview"],
        img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
