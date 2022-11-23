from ls_addon import ADDON_ICON as ADDON_ICON


def update_listitem(listitem, variables):
    item_type = variables['ITEM_TYPE']
    thumb = variables['COVERS'].split('\n')[0]
    info = dict()
    info['title'] = variables['NAME']
    info['duration'] = int(variables['DURATION_MS']) // 1000

    if item_type == 'Track':
        info['album'] = variables['ALBUM']
        info['artist'] = variables['ARTISTS'].replace('\n', ', ')
        info['albumArtist'] = variables['ALBUM_ARTISTS'].replace('\n', ', ')
    elif item_type == 'Episode':
        info['artist'] = variables['SHOW_NAME']
        info['releaseDate'] = variables['RELEASE_DATE']
    else:
        info['artist'] = "Unknown"
        thumb = ADDON_ICON
    listitem.setArt(dict(fanart=thumb, thumb=thumb))
    listitem.setInfo('music', info)
