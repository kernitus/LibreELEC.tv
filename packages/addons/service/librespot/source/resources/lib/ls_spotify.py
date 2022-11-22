from ls_addon import ADDON_ICON as ADDON_ICON

def update_listitem(listitem, type):
    title = os.environ['NAME']
    thumb = os.environ['COVERS'].split('\n')[0]
    if type == 'Track':
        album = os.environ['ALBUM']
        artist = os.environ['ARTISTS']
    elif type == 'Episode':
        album = os.environ['SHOW_NAME']
        artist = "ARTISTA"
    else:
        album = ''
        artist = 'Unknown Media Type'
        thumb = ADDON_ICON
        title = ''
    listitem.setArt(dict(fanart=thumb, thumb=thumb))
    listitem.setInfo('music', dict(
        album=album, artist=artist, title=title))
    print('{}#{}#{}#{}'.format(title, artist, album, thumb))