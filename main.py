from yaml import safe_load, YAMLError

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify, SpotifyException

from textual.app import App, ComposeResult
from textual.widgets import Header, Input, Static, Footer
from rich.table import Table

import itertools
from collections import defaultdict

from datetime import timedelta

class Setup:

    @staticmethod
    def load_config(path: str) -> dict:

        with open(path, "r") as stream:
            try:
                return safe_load(stream)
            except YAMLError as error:
                print(error)

        return None

    @staticmethod
    def setup_spotify(client_id: str, client_secret: str, redirect_uri: str, scope: str) -> Spotify:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )

        return Spotify(auth_manager=auth_manager)


class Utils:

    @staticmethod
    def merge(shared_key, *iterables):
        result = defaultdict(dict)
        for dictionary in itertools.chain.from_iterable(iterables):
            result[dictionary[shared_key]].update(dictionary)
        for dictionary in result.values():
            dictionary.pop(shared_key)
        return result


class Backend:

    def __init__(self, spotify: Spotify):
        self.spotify = spotify

    def __format(self, data: dict):

        artists = lambda d: list( i["name"] for i in d["artists"])
        artists_string = lambda d: ", ".join(artists(d))

        to_percent = lambda f: f"{ round(f * 100, 1) }%"
        to_bpm = lambda t: f"{ round(t, 1)}bpm"
        to_time = lambda t: str(timedelta(milliseconds=t))
        x_or_o = lambda s: "y" if s else "n"

        return {
            "name": data['name'],
            "artists": artists_string(data),
            "duration": to_time(data["duration_ms"]),
            "explicit": x_or_o(data["explicit"]),
            "tempo": to_bpm(data["tempo"]),
            "energy": to_percent(data["energy"]),
            "danceability": to_percent(data["danceability"])
        }

    def get_playlist_info(self, playlist_url: str):
        results = self.spotify.playlist_tracks(playlist_id=playlist_url)
        track_infos = list( i["track"] for i in results["items"] )

        track_ids = list( i["id"] for i in track_infos )
        track_analytics = self.spotify.audio_features(track_ids)

        merged_values = Utils.merge("id", track_infos, track_analytics).values()

        return (self.__format(i) for i in merged_values)

    def get_track_info(self, track_url: str):
        track_info = self.spotify.track(track_id=track_url)
        track_analytics = self.spotify.audio_features(track_info["id"])

        merged_values = track_info.copy()
        merged_values.update(track_analytics[0])

        return self.__format(merged_values)


class Analyzer(App):

  BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

  def __init__(self, spotify: Spotify):
    super().__init__()

    self.spotify = spotify
    self.backend = Backend(spotify)

  def compose(self) -> ComposeResult:
    yield Header()
    yield Input(placeholder="Spotify URL")
    yield Static(id="results")
    yield Footer()

  def action_toggle_dark(self) -> None:
    self.dark = not self.dark

  async def on_input_submitted(self, message: Input.Submitted) -> None:
    static = self.query_one("#results", Static)

    try:

        if "track" in message.value:
            data = [self.backend.get_track_info(message.value)]
        elif "playlist" in message.value:
            data = self.backend.get_playlist_info(message.value)
        else:
            raise SpotifyException

    except SpotifyException:
      static.update("Error: Invalid URL")
      return 
  
    columns = ("Name", "Artist", "Time", "Explicit", "Tempo", "Energy", "Danceability")

    table = Table(*columns)

    for row in data:
        table.add_row(*tuple(row.values()))

    static.update(table)


if __name__ == "__main__":

  config = Setup.load_config("config.yml")

  spotify = Setup.setup_spotify(
      config['spotify']['client_id'], 
      config['spotify']['client_secret'],
      config['spotify']['redirect_uri'],
      "user-library-read"
  )
  
  analyzer_app = Analyzer(spotify)
  analyzer_app.run()
