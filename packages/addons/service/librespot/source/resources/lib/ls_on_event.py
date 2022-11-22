#!/usr/bin/python3

import os
import json

PIPE_PATH = "/tmp/librespot"


def main():
    event = os.environ['PLAYER_EVENT']
    print(f'Captured event: {event}')

    json_dict = {
        'event': event
    }

    dumped = json.dumps(json_dict, indent=None)

    # if event == "track_changed":
    #    self.on_track_changed()
    # if event == "playing":
    #    self.on_event_playing()
    # if event == "paused":
    #    self.on_event_paused()
    # if event == "stopped":
    #    self.on_event_stopped()

    # Open named unix socket
    path = "/tmp/librespot"
    try:
        os.mkfifo(path)
    except OSError as e:
        print(f'File already exists')

    with open(PIPE_PATH, 'a') as fifo:
        print(f'Writing to pipe: {dumped}')
        fifo.write(dumped)
        fifo.write('\n')
        fifo.close()


def on_track_changed(self):
    item_type = os.environ['ITEM_TYPE']
    track_id = os.environ['TRACK_ID']
    name = os.environ['NAME']
    print(f'event track changed id: {track_id}, {name}')


if __name__ == "__main__":
    main()
