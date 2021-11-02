import os
import sys


import click
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy


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

    musics = [
        {'song_name': '一路向北', 'year': '1988', 'singer': 'Jay Chou'},
        {'song_name': '一路向北', 'year': '1925', 'singer': 'Jay Chou'},
        {'song_name': '一路向北', 'year': '1922', 'singer': 'Jay Chou'},
    ]
    for m in musics:
        music = Music(song_name=m['song_name'], year=m['year'], singer=m['singer'])
        db.session.add(music)
    
    import pandas as pd
    singerDF = pd.read_csv("./data/singer.csv", dtype=str)
    for row in singerDF.itertuples():
        singer = Singer(singer=row[2], gender=row[3] ,language=row[4])
        db.session.add(singer)

    db.session.commit()
    click.echo('Done.')


class Music(db.Model):
    __tablename__ = 'music'

    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(50))
    year = db.Column(db.String(4))
    singer = db.Column(db.String(50))

class Singer(db.Model):
    __tablename__ = 'singer'
        
    id = db.Column(db.Integer, primary_key=True)
    singer = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    language = db.Column(db.String(30))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        song_name = request.form['song_name']
        year = request.form['year']
        singer = request.form['singer']

        # if not title or not year or len(year) > 4 or len(title) > 60:
        #     flash('Invalid input.')
        #     return redirect(url_for('index'))

        music = Music(song_name=song_name, year=year, singer=singer)
        db.session.add(music)
        db.session.commit()
        flash('Item created.')
        return redirect(url_for('index'))

    musics = Music.query.all()
    return render_template('index.html', musics=musics)

@app.route('/singer', methods=['GET', 'POST'])
def SingerPage():
    # if request.method == 'POST':
    #     song_name = request.form['song_name']
    #     year = request.form['year']
    #     singer = request.form['singer']

    #     # if not title or not year or len(year) > 4 or len(title) > 60:
    #     #     flash('Invalid input.')
    #     #     return redirect(url_for('index'))

    #     music = Music(song_name=song_name, year=year, singer=singer)
    #     db.session.add(music)
    #     db.session.commit()
    #     flash('Item created.')
    #     return redirect(url_for('index'))

    singers = Singer.query.all()
    return render_template('SingerPage.html', singers=singers)

@app.route('/music/edit/<int:music_id>', methods=['GET', 'POST'])
def edit(music_id):
    music = Music.query.get_or_404(music_id)

    if request.method == 'POST':
        song_name = request.form['song_name']
        year = request.form['year']
        singer = request.form['singer']

        # if not title or not year or len(year) > 4 or len(title) > 60:
        #     flash('Invalid input.')
        #     return redirect(url_for('edit', movie_id=movie_id))

        music.song_name = song_name
        music.year = year   
        music.singer = singer
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('index'))

    return render_template('edit.html', music=music)


@app.route('/delete/<int:music_id>', methods=['POST'])
def delete(music_id):
    music = Music.query.get_or_404(music_id)
    db.session.delete(music)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)