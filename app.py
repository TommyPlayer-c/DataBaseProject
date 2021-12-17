import os
import sys
import csv

import click
from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import and_


count = 12
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/music'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)
cur_user = '你好'
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

    singerDF = pd.read_csv("./data/singer2.csv", dtype=str)  # 这里添加了生日、星座
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
        user = User(user_name=row[2], user_gender=row[3],
                    type=row[4], password=row[5])
        db.session.add(user)
    db.session.commit()

    albumDF = pd.read_csv("./data/album.csv", dtype=str)
    for row in albumDF.itertuples():
        alb = Album(album_name=row[1], year=row[2],
                    song_num=row[3], singer_name=row[4], album_fig=row[5])
        db.session.add(alb)
    db.session.commit()

    click.echo('Done.')


class Music(db.Model):
    __tablename__ = 'music'

    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(50))
    type = db.Column(db.String(20), db.ForeignKey(
        "type.type_name", ondelete='CASCADE'))
    singer_name = db.Column(db.String(50), db.ForeignKey(
        "singer.singer_name", ondelete='CASCADE'))
    url = db.Column(db.String(100))
    song_fig = db.Column(db.String(200))


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
    password = db.Column(db.String(20))
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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form.get('username')
    password = request.form.get('password')
    global cur_user
    cur_user = username
    Result = User.query.filter(
        and_(User.user_name == username, User.password == password))
    if Result.count() == 1:
        return redirect(url_for('index'))
    else:
        flash('登录失败!用户名或密码错误')
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    global count
    count = count + 1
    username = request.form.get('username')
    password = request.form.get('password')
    gender = request.form.get('sex')
    type = request.form.get('like')
    user = User(user_id=count, user_name=username,
                user_gender=gender, type=type, password=password)
    db.session.add(user)
    db.session.commit()
    flash('注册成功')
    return render_template('register.html')


@app.route('/music', methods=['GET', 'POST'])
def index():
    page = int(request.args.get('page', 1))
    if request.method == 'POST':
        song_name = request.form['song_name']
        type = request.form['type']
        singer_name = request.form['singer_name']
        song_fig = request.form['song_fig']
        url = request.form['song_url']
        typeResult = Type.query.filter(Type.type_name == type)
        singerResult = Singer.query.filter(Singer.singer_name == singer_name)
        if typeResult.count() == 0 or singerResult.count() == 0:
            flash('index:Invalid input.')
            return redirect(url_for('index'))

        music = Music(song_name=song_name, type=type,
                      singer_name=singer_name, song_fig=song_fig, url=url)
        db.session.add(music)
        db.session.commit()
        flash('增加成功！')
        return redirect(url_for('index'))

    paginate = Music.query.order_by(Music.id).paginate(page=page, per_page=10)
    musics = paginate.items
    global cur_user
    return render_template('index.html', musics=musics, paginate=paginate,cur_user=cur_user)


@app.route('/singer', methods=['GET', 'POST'])
def SingerPage():
    page = int(request.args.get('page', 1))
    if request.method == 'POST':
        singer_name = request.form['singer_name']
        gender = request.form['gender']
        language = request.form['language']
        birthday = request.form['birthday']
        constellation = request.form['constellation']
        languageResult = Language.query.filter(
            Language.language_name == language)
        if languageResult.count() == 0:
            flash('singerpage:Invalid input.')
            return redirect(url_for('SingerPage'))

        singer = Singer(singer_name=singer_name,
                        gender=gender, language=language, singer_fig='images/singer/01.jpg', birthday=birthday, constellation=constellation)
        db.session.add(singer)
        db.session.commit()
        flash('增加成功！')
        return redirect(url_for('SingerPage'))

    paginate = Singer.query.order_by(
        Singer.singer_name).paginate(page=page, per_page=8)
    singers = paginate.items
    global cur_user
    return render_template('SingerPage.html', singers=singers, paginate=paginate,cur_user=cur_user)


@app.route('/user', methods=['GET', 'POST'])
def UserPage():
    users = User.query.all()
    global cur_user
    return render_template('UserPage.html', users=users,cur_user=cur_user)


@app.route('/album', methods=['GET', 'POST'])
def AlbumPage():
    page = int(request.args.get('page', 1))
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

    paginate = Album.query.order_by(
        Album.album_name).paginate(page=page, per_page=6)
    albums = paginate.items
    global cur_user
    return render_template('AlbumPage.html', albums=albums, paginate=paginate,cur_user=cur_user)


@app.route('/edit/music/<int:music_id>', methods=['GET', 'POST'])
def EditMusic(music_id):
    global cur_user
    music = Music.query.get_or_404(music_id)

    if request.method == 'POST':
        song_name = request.form['song_name']
        url = request.form['song_url']
        type = request.form['type']
        singer_name = request.form['singer_name']

        typeResult = Type.query.filter(Type.type_name == type)
        singerResult = Singer.query.filter(Singer.singer_name == singer_name)
        if typeResult.count() == 0 or singerResult.count() == 0:
            flash('非法修改')
            return redirect(url_for('index'))

        music.song_name = song_name
        music.type = type
        music.singer_name = singer_name
        music.url = url
        db.session.commit()
        flash('更新成功！')
        return redirect(url_for('index'))
    return render_template('EditMusic.html', music=music,cur_user=cur_user)


@app.route('/singer/edit/<string:singer_name>', methods=['GET', 'POST'])
def EditSinger(singer_name):
    global cur_user
    singer = Singer.query.get_or_404(singer_name)

    if request.method == 'POST':
        singer_name = request.form['singer_name']
        gender = request.form['gender']
        language = request.form['language']
        birthday = request.form['birthday']
        constellation = request.form['constellation']

        languageResult = Language.query.filter(
            Language.language_name == language)
        if languageResult.count() == 0:
            flash('editsinger:非法修改')
            return redirect(url_for('SingerPage'))

        singer.singer_name = singer_name
        singer.gender = gender
        singer.language = language
        singer.birthday = birthday
        singer.constellation = constellation
        db.session.commit()
        flash('更新成功！')
        return redirect(url_for('SingerPage'))
    return render_template('EditSinger.html', singer=singer,cur_user=cur_user)


@app.route('/album/edit/<string:album_name>', methods=['GET', 'POST'])
def EditAlbum(album_name):
    global cur_user
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
        flash('更新成功!')
        return redirect(url_for('AlbumPage'))
    return render_template('EditAlbum.html', album=album,cur_user=cur_user)


@app.route('/music/delete/<int:music_id>', methods=['POST'])
def DeleteMusic(music_id):
    music = Music.query.get_or_404(music_id)
    db.session.delete(music)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('index'))


@app.route('/singer/delete/<string:singer_name>', methods=['POST'])
def DeleteSinger(singer_name):
    singer = Singer.query.get_or_404(singer_name)
    db.session.delete(singer)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('SingerPage'))


@app.route('/album/delete/<string:album_name>', methods=['POST'])
def DeleteAlbum(album_name):
    album = Album.query.get_or_404(album_name)
    db.session.delete(album)
    db.session.commit()
    flash('删除成功！')
    return redirect(url_for('AlbumPage'))


@app.route('/music/search/', methods=['GET', 'POST'])
def SearchMusic():
    global cur_user
    if request.method == 'POST':
        song_name = request.form['song_name']
        type = request.form['type']
        singer_name = request.form['singer_name']
        music_list = db.session.query(Music)
        if song_name:
            music_list = music_list.filter(Music.song_name == song_name)
        if type != "不限":
            music_list = music_list.filter(Music.type == type)
        if singer_name:
            music_list = music_list.filter(Music.singer_name == singer_name)

        music_list = music_list.all()
        if music_list == None:
            flash('没有找到！')
            return redirect(url_for('index.html'))
        return render_template('index.html', musics=music_list, paginate=None,cur_user=cur_user)
    return render_template('index.html', musics=None, paginate=None,cur_user=cur_user)


@app.route('/music/Add/', methods=['POST'])
def AddMusic():
    song_name = request.form['song_name']
    type = request.form['type']
    singer_name = request.form['singer_name']
    url = request.form['song_url']
    typeResult = Type.query.filter(Type.type_name == type)
    singerResult = Singer.query.filter(Singer.singer_name == singer_name)
    if typeResult.count() == 0 or singerResult.count() == 0:
        flash('index:Invalid input.')
        return redirect(url_for('index'))

    music = Music(song_name=song_name, type=type,
                  singer_name=singer_name, song_fig='images/song/01.jpg', url=url)
    db.session.add(music)
    db.session.commit()
    flash('增加成功！')
    return redirect(url_for('index'))


@app.route('/singer/filter/', methods=['POST'])
def FilterSinger():
    global cur_user
    singer_name = request.form['singer_name']
    singer_sex = request.form['singer_sex']
    singer_area = request.form['area']
    constellation = request.form['constellation']
    singer_list = db.session.query(Singer)
    if singer_name:
        singer_list = singer_list.filter(Singer.singer_name == singer_name)
    if singer_sex != "不限":
        singer_list = singer_list.filter(Singer.gender == singer_sex)
    if singer_area != "不限":
        singer_list = singer_list.filter(Singer.language == singer_area)
    if constellation != "不限":
        singer_list = singer_list.filter(Singer.constellation == constellation)
    singer_list = singer_list.all()
    if singer_list == None:
        flash('没有找到！')
        return redirect(url_for('SingerPage'))
    return render_template('SingerPage.html', singers=singer_list, paginate=None,cur_user=cur_user)


@app.route('/album/search/', methods=['GET', 'POST'])
def SearchAlbum():
    global cur_user
    if request.method == 'POST':
        album_name = request.form['album_name']
        year = request.form['year']
        singer_name = request.form['singer_name']
        lower_song_num = request.form.get('lower_song_num',type=int)
        upper_song_num = request.form.get('upper_song_num',type=int)
        
        album_list = db.session.query(Album)
        if album_name:
            album_list = album_list.filter(Album.album_name == album_name)
        if year:
            album_list = album_list.filter(Album.year == year)
        if singer_name:
            album_list = album_list.filter(Album.singer_name == singer_name)
        album_list = album_list.all()
        temp = album_list
        if lower_song_num and temp != None:
            res = []
            for i in range(len(temp)):
                if temp[i].song_num >= lower_song_num:
                    res.append(temp[i])
            temp = res
        if upper_song_num and temp != None:
            res = []
            for i in range(len(temp)):
                if temp[i].song_num <= upper_song_num:
                    res.append(temp[i])
            temp = res
        album_list = temp
        if album_list == None:
            flash('没有找到！')
            return redirect(url_for('AlbumPage'))
        return render_template('AlbumPage.html', albums=album_list, paginate=None,cur_user=cur_user)
    return render_template('AlbumPage.html', albums=None, paginate=None,cur_user=cur_user)


@app.route('/ShowSinger/<string:singer_name>', methods=['GET', 'POST'])
def ShowSinger(singer_name):
    global cur_user
    singer = Singer.query.get_or_404(singer_name)
    songs = Music.query.filter(Music.singer_name == singer_name)
    return render_template('ShowSinger.html', singer=singer, songs=songs,cur_user=cur_user)


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'dev'
    app.run(debug=True)
