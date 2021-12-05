import pandas as pd

arr = []
for i in range(30):
    if i < 10:
        x = '0' + str(i+1)
    else:
        x = str(i+1)
    arr.append('images/album/'+x+'.jpg')
album = pd.read_csv('data/album.csv')
album['album_fig'] = arr
album.to_csv('data/album.csv', index=None, encoding='utf8') 

arr = []
for i in range(30):
    if i < 10:
        x = '0' + str(i+1)
    else:
        x = str(i+1)
    arr.append('images/singer/'+x+'.jpg')
singer = pd.read_csv('data/singer.csv')
singer['singer_fig'] = arr
singer.to_csv('data/singer.csv', index=None, encoding='utf8')

arr = []
for i in range(100):
    if i < 10:
        x = '0' + str(i+1)
    else:
        x = str(i+1)
    arr.append('images/song/'+x+'.jpg')
song = pd.read_csv('data/song.csv')
print(song['url'][0])
song['song_fig'] = arr
song.to_csv('data/song.csv', index=None, encoding='utf8')

