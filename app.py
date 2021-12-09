import os
import sys


import click
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import and_
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/music'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)

###########################################################################
#                       下面为自定义命令                                    #
###########################################################################
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

    singerDF = pd.read_csv("./data/singer2.csv", dtype=str) # 这里添加了生日、星座
    for row in singerDF.itertuples():
        singer = Singer(
            singer_name=row[1], gender=row[2], birthday=row[3], constellation=row[4], language=row[5], singer_fig=row[6])
        db.session.add(singer)
    db.session.commit()

    musicsDF = pd.read_csv("./data/song.csv", dtype=str)
    for row in musicsDF.itertuples():
        music = Music(song_name=row[2], type=row[3],
                      singer_name=row[4], url=row[5], song_fig=row[6])
        db.session.add(music)
    db.session.commit()

    userDF = pd.read_csv("./data/user.csv", dtype=str)
    for row in userDF.itertuples():
        user = User(user_name=row[2], user_gender=row[3], type=row[4])
        db.session.add(user)
    db.session.commit()

    albumDF = pd.read_csv("./data/album.csv", dtype=str)
    for row in albumDF.itertuples():
        alb = Album(album_name=row[1], year=row[2],
                    song_num=row[3], singer_name=row[4], album_fig=row[5])
        db.session.add(alb)
    db.session.commit()

    click.echo('Done.')

###########################################################################
#                       下面为数据库模型类                                  #
###########################################################################


class Music(db.Model):
    __tablename__ = 'music'

    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(50))
    type = db.Column(db.String(20), db.ForeignKey(
        "type.type_name", ondelete='CASCADE'))
    singer_name = db.Column(db.String(50), db.ForeignKey(
        "singer.singer_name", ondelete='CASCADE'))
    url = db.Column(db.String(100))
    song_fig = db.Column(db.String(50))


class Singer(db.Model):
    __tablename__ = 'singer'

    singer_name = db.Column(db.String(50), primary_key=True)
    gender = db.Column(db.String(20))
    language = db.Column(db.String(30), db.ForeignKey(
        "language.language_name", ondelete='CASCADE'))
    singer_song = db.relationship(
        'Music', backref='Singer', cascade='all, delete-orphan', passive_deletes=True)
    singer_album = db.relationship(
        'Album', backref='Singer', cascade='all, delete-orphan', passive_deletes=True)
    singer_fig = db.Column(db.String(50))
    birthday = db.Column(db.String(20))
    constellation = db.Column(db.String(20))


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
    type = db.Column(db.String(20), db.ForeignKey(
        "type.type_name", ondelete='CASCADE'))


class Album(db.Model):
    __tablename__ = 'album'

    album_name = db.Column(db.String(50), primary_key=True)
    year = db.Column(db.Integer)
    song_num = db.Column(db.Integer)
    singer_name = db.Column(db.String(50), db.ForeignKey(
        "singer.singer_name", ondelete='CASCADE'))
    album_fig = db.Column(db.String(50))


###########################################################################
#                       下面为视图函数                                     #
###########################################################################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        song_name = request.form['song_name']
        type = request.form['type']
        singer_name = request.form['singer_name']

        typeResult = Type.query.filter(Type.type_name == type)
        singerResult = Singer.query.filter(Singer.singer_name == singer_name)
        if typeResult.count() == 0 or singerResult.count() == 0:
            flash('index:Invalid input.')
            return redirect(url_for('index'))

        music = Music(song_name=song_name, type=type, singer_name=singer_name, song_fig='images/song/01.jpg')
        db.session.add(music)
        db.session.commit()
        flash('增加成功！')
        return redirect(url_for('index'))

    musics = Music.query.order_by(Music.id).all()
    return render_template('index.html', musics=musics)


@app.route('/singer', methods=['GET', 'POST'])
def SingerPage():
    if request.method == 'POST':
        singer_name = request.form['singer_name']
        gender = request.form['gender']
        language = request.form['language']

        languageResult = Language.query.filter(
            Language.language_name == language)
        if languageResult.count() == 0:
            flash('singerpage:Invalid input.')
            return redirect(url_for('SingerPage'))

        singer = Singer(singer_name=singer_name,
                        gender=gender, language=language, singer_fig='images/singer/01.jpg')
        db.session.add(singer)
        db.session.commit()
        flash('增加成功！')
        return redirect(url_for('SingerPage'))

    singers = Singer.query.all()
    return render_template('SingerPage.html', singers=singers)


@app.route('/user', methods=['GET', 'POST'])
def UserPage():
    users = User.query.all()
    return render_template('UserPage.html', users=users)


@app.route('/album', methods=['GET', 'POST'])
def AlbumPage():
    if request.method == 'POST':
        album_name = request.form['album_name']
        year = request.form['year']
        song_num = request.form['song_num']
        singer_name = request.form['singer_name']

        singerResult = Singer.query.filter(Singer.singer_name == singer_name)
        if singerResult.count() == 0:
            flash('albumpage:Invalid input.')
            return redirect(url_for('AlbumPage'))

        album = Album(album_name=album_name, year=year,
                      song_num=song_num, singer_name=singer_name, album_fig='images/album/01.jpg')
        db.session.add(album)
        db.session.commit()
        flash('增加成功！')
        return redirect(url_for('AlbumPage'))

    albums = Album.query.all()
    return render_template('AlbumPage.html', albums=albums)


@app.route('/edit/music/<int:music_id>', methods=['GET', 'POST'])
def EditMusic(music_id):
    music = Music.query.get_or_404(music_id)

    if request.method == 'POST':
        song_name = request.form['song_name']
        type = request.form['type']
        singer_name = request.form['singer_name']

        typeResult = Type.query.filter(Type.type_name==type)
        singerResult = Singer.query.filter(Singer.singer_name==singer_name)
        if typeResult.count() == 0 or singerResult.count() == 0:
            flash('非法修改')
            return redirect(url_for('index'))

        music.song_name = song_name
        music.type = type   
        music.singer_name = singer_name
        db.session.commit()
        flash('更新成功！')
        return redirect(url_for('index'))

    return render_template('EditMusic.html', music=music)


@app.route('/singer/edit/<string:singer_name>', methods=['GET', 'POST'])
def EditSinger(singer_name):
    singer = Singer.query.get_or_404(singer_name)

    if request.method == 'POST':
        singer_name = request.form['singer_name']
        gender = request.form['gender']
        language = request.form['language']

        languageResult = Language.query.filter(
            Language.language_name == language)
        if languageResult.count() == 0:
            flash('editsinger:非法修改')
            return redirect(url_for('SingerPage'))

        singer.singer_name = singer_name
        singer.gender = gender
        singer.language = language
        db.session.commit()
        flash('更新成功！')
        return redirect(url_for('SingerPage'))

    return render_template('EditSinger.html', singer=singer)


@app.route('/album/edit/<string:album_name>', methods=['GET', 'POST'])
def EditAlbum(album_name):
    album = Album.query.get_or_404(album_name)

    if request.method == 'POST':
        album_name = request.form['album_name']
        year = request.form['year']
        song_num = request.form['song_num']
        singer_name = request.form['singer_name']

        singerResult = Singer.query.filter(Singer.singer_name == singer_name)
        if singerResult.count() == 0:
            flash('editalbum:非法修改')
            return redirect(url_for('AlbumPage'))

        album.album_name = album_name
        album.year = year
        album.song_num = song_num
        album.singer_name = singer_name
        db.session.commit()
        flash('更新成功！')
        return redirect(url_for('AlbumPage'))

    return render_template('EditAlbum.html', album=album)


@app.route('/music/delete/<int:music_id>', methods=['POST'])
def DeleteMusic(music_id):
    music = Music.query.get_or_404(music_id)
    db.session.delete(music)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('index'))
    # return redirect(request.referrer)


@app.route('/singer/delete/<string:singer_name>', methods=['POST'])
def DeleteSinger(singer_name):
    singer = Singer.query.get_or_404(singer_name)
    db.session.delete(singer)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('SingerPage'))
    # return redirect(request.referrer)


@app.route('/album/delete/<string:album_name>', methods=['POST'])
def DeleteAlbum(album_name):
    album = Album.query.get_or_404(album_name)
    db.session.delete(album)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('AlbumPage'))
    # return redirect(request.referrer)


@app.route('/music/search/', methods=['GET', 'POST'])
def SearchMusic():
    if request.method == 'POST':
        song_name = request.form['song_name']
        music_item = Music.query.filter(
            Music.song_name == song_name).first()     # 获取对象要使用first函数！
        if music_item == None:
            flash('没有找到！')
            return redirect(url_for('SearchMusic'))
        # return "查询成功!<br>歌曲名：%s 歌手：%s 类型：%s" %(music_item.song_name, music_item.singer_name, music_item.type)
        return render_template('SearchMusic.html', music=music_item)
    return render_template('index.html', music=None)


@app.route('/music/Add/', methods=['POST'])
def AddMusic():
    song_name = request.form['song_name']
    type = request.form['type']
    singer_name = request.form['singer_name']

    typeResult = Type.query.filter(Type.type_name == type)
    singerResult = Singer.query.filter(Singer.singer_name == singer_name)
    if typeResult.count() == 0 or singerResult.count() == 0:
        flash('Invalid input.')
        return redirect(url_for('index'))
    music = Music(song_name=song_name, type=type, singer_name=singer_name, song_fig='images/song/01.jpg')
    db.session.add(music)
    db.session.commit()
    flash('增加成功！')
    return redirect(url_for('index'))


@app.route('/singer/search/', methods=['GET', 'POST'])
def SearchSinger():
    if request.method == 'POST':
        singer_name = request.form['singer_name']
        singer_item = Singer.query.filter(
            Singer.singer_name == singer_name).first()     # 获取对象要使用first函数！
        if singer_item == None:
            flash('没有找到！')
            return redirect(url_for('SearchSinger'))
        # return "查询成功!<br>歌曲名：%s 歌手：%s 类型：%s" %(music_item.song_name, music_item.singer_name, music_item.type)
        return render_template('SearchSinger.html', singer=singer_item)
    return render_template('SearchSinger.html', singer=None)


@app.route('/singer/filter/', methods=['POST'])
def FilterSinger():
    singer_name = request.form['singer_name']
    singer_sex = request.form['singer_sex']
    singer_area = request.form['area']
    singer_list = Singer.query.filter(
        and_(Singer.singer_name == singer_name, Singer.gender == singer_sex, Singer.language == singer_area)).all()
    return render_template('SingerPage.html', singers=singer_list)


@app.route('/album/search/', methods=['GET', 'POST'])
def SearchAlbum():
    if request.method == 'POST':
        album_name = request.form['album_name']
        album = Album.query.filter(Album.album_name == album_name).all()

        if album == None:
            flash('没有找到！')
            return redirect(url_for('AlbumPage'))
        return render_template('AlbumPage.html', albums=album)
    return render_template('AlbumPage.html', albums=None)


# route()装饰器用于将URL绑定到函数
@app.route('/ShowSinger/<string:singer_name>', methods=['GET', 'POST'])
def ShowSinger(singer_name):
    singer = Singer.query.get_or_404(singer_name)
    songs = Music.query.filter(Music.singer_name == singer_name)
    return render_template('ShowSinger.html', singer=singer, songs=songs)


###########################################################################
#                       下面为主函数（debug模式）                           #
###########################################################################
if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'dev'
    app.run(debug=True)
