import os
import sys


import click
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/music'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    # 这里创建表时要注意顺序
    langDF = pd.read_csv("./data/language.csv", dtype=str)
    for row in langDF.itertuples():
        langrow = Language(language_name=row[1], area=row[2])
        db.session.add(langrow)
    db.session.commit()

    typeDF = pd.read_csv("./data/type.csv", dtype=str)
    for row in typeDF.itertuples():
        typerow = Type(type_name=row[1], popular_rate=row[2])
        db.session.add(typerow)
    db.session.commit()

    singerDF = pd.read_csv("./data/singer.csv", dtype=str)
    for row in singerDF.itertuples():
        singer = Singer(singer_name=row[1], gender=row[2] ,language=row[3])
        db.session.add(singer)
    db.session.commit()

    musicsDF = pd.read_csv("./data/song.csv", dtype=str)
    for row in musicsDF.itertuples():
        music = Music(song_name=row[2], type=row[3], singer_name=row[4], url=row[5])
        db.session.add(music)
    db.session.commit()

    userDF = pd.read_csv("./data/user.csv", dtype=str)
    for row in userDF.itertuples():
        user = User(user_name=row[2], user_gender=row[3], type=row[4])
        db.session.add(user)
    db.session.commit()

    albumDF = pd.read_csv("./data/album.csv", dtype=str)
    for row in albumDF.itertuples():
        alb = Album(album_name=row[1], year=row[2], song_num=row[3], singer_name=row[4])
        db.session.add(alb)
    db.session.commit()

    click.echo('Done.')


class Music(db.Model):
    __tablename__ = 'music'

    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(50))
    type = db.Column(db.String(20), db.ForeignKey("type.type_name"))
    singer_name = db.Column(db.String(50), db.ForeignKey("singer.singer_name"))
    url = db.Column(db.String(100))

class Singer(db.Model):
    __tablename__ = 'singer'
        
    # singer_id = db.Column(db.Integer, primary_key=True)
    singer_name = db.Column(db.String(50), primary_key=True)
    gender = db.Column(db.String(20))
    language = db.Column(db.String(30), db.ForeignKey("language.language_name"))

class Type(db.Model):
    __tablename__ = 'type'
        
    type_name = db.Column(db.String(20), primary_key=True)
    popular_rate = db.Column(db.Float)


class Language(db.Model):
    __tablename__ = 'language'
        
    language_name = db.Column(db.String(30), primary_key=True)
    area = db.Column(db.String(20))


class User(db.Model):
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    user_gender = db.Column(db.String(20))
    type = db.Column(db.String(20), db.ForeignKey("type.type_name"))


class Album(db.Model):
    __tablename__ = 'album'
    
    album_name = db.Column(db.String(50), primary_key=True)
    year = db.Column(db.Integer)
    song_num = db.Column(db.Integer, db.ForeignKey("music.id"))
    singer_name = db.Column(db.String(50), db.ForeignKey("singer.singer_name"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        song_name = request.form['song_name']
        type = request.form['type']
        singer_name = request.form['singer_name']

        # typeResult = Type.query.filter(Type.type_name==type)
        # singerResult = Singer.query.filter(Singer.singer_name==singer_name)
        # if typeResult is None or singerResult is None:
        #     flash('Invalid input.')
        #     return redirect(url_for('index'))

        music = Music(song_name=song_name, type=type, singer_name=singer_name)
        db.session.add(music)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    musics = Music.query.all()
    return render_template('index.html', musics=musics)

@app.route('/singer', methods=['GET', 'POST'])
def SingerPage():
    if request.method == 'POST':
        singer_name = request.form['singer_name']
        gender = request.form['gender']
        language = request.form['language']

        # typeResult = Type.query.filter(Type.type_name==type)
        # singerResult = Singer.query.filter(Singer.singer_name==singer_name)
        # if typeResult is None or singerResult is None:
        #     flash('Invalid input.')
        #     return redirect(url_for('index'))

        singer = Singer(singer_name=singer_name, gender=gender, language=language)
        db.session.add(singer)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('SingerPage'))

    singers = Singer.query.all()
    return render_template('SingerPage.html', singers=singers)


@app.route('/user', methods=['GET', 'POST'])
def UserPage():
    users = User.query.all()
    return render_template('UserPage.html', users=users)


@app.route('/album', methods=['GET', 'POST'])
def AlbumPage():
    albums = Album.query.all()
    songs = db.session.query(Music).join(Album)
    return render_template('AlbumPage.html', albumsAndsongs=zip(albums,songs))

@app.route('/music/edit/<int:music_id>', methods=['GET', 'POST'])
def edit(music_id):
    music = Music.query.get_or_404(music_id)

    if request.method == 'POST':
        song_name = request.form['song_name']
        # type = request.form['type']
        # singer_name = request.form['singer_name']

        # if not title or not type or len(type) > 4 or len(title) > 60:
        #     flash('Invalid input.')
        #     return redirect(url_for('edit', movie_id=movie_id))

        music.song_name = song_name
        # music.type = type   
        # music.singer_name = singer_name
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))

    return render_template('edit.html', music=music)


@app.route('/music/delete/<int:music_id>', methods=['POST'])
def delete(music_id):
    music = Music.query.get_or_404(music_id)
    db.session.delete(music)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))
    # return redirect(request.referrer)

@app.route('/singer/delete/<string:singer_name>', methods=['POST'])
def DeleteSinger(singer_name):
    singer = Singer.query.get_or_404(singer_name)
    db.session.delete(singer)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('SingerPage'))
    # return redirect(request.referrer)

@app.route('/ShowSinger/<string:singer_name>', methods=['GET', 'POST'])
def ShowSinger(singer_name):
    singer = Singer.query.get_or_404(singer_name)
    songs = Music.query.filter(Music.singer_name==singer_name)
    return render_template('ShowSinger.html', singer=singer, songs=songs)

if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'dev'
    app.run(debug=True)