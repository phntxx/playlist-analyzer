from yaml import safe_load, YAMLError

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify, SpotifyException

from textual.app import App, ComposeResult
from textual.containers import Content
from textual.widgets import Header, Input, Static, Footer
from rich.table import Table

import itertools
from collections import defaultdict

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

    def get_playlist_info(self, playlist_url: str):
        results = self.spotify.playlist_tracks(playlist_id=playlist_url)
        track_infos = list( i["track"] for i in results["items"] )

        track_ids = list( i["id"] for i in track_infos )
        track_analytics = self.spotify.audio_features(track_ids)

        merged_values = Utils.merge("id", track_infos, track_analytics).values()

        return merged_values


class Analyzer(App):

  BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

  def __init__(self, spotify: Spotify):
    super().__init__()

    self.spotify = spotify
    self.backend = Backend(spotify)

  def compose(self) -> ComposeResult:
    yield Header()
    yield Input(placeholder="Spotify playlist URL")
    yield Static(id="results")
    yield Footer()

  def action_toggle_dark(self) -> None:
    self.dark = not self.dark

  async def on_input_submitted(self, message: Input.Submitted) -> None:

    try:
      data = self.backend.get_playlist_info(message.value)
    except SpotifyException:
      self.panic("Error: Invalid URL")
      quit()

    artists = lambda d: list( i["name"] for i in d["artists"])
    artists_string = lambda d: ", ".join(artists(d))

    columns = ("Name", "Artist", "Time", "Explicit", "Tempo", "Energy", "Danceability")
    rows = ((i["name"], artists_string(i), str(i["duration_ms"]), "x" if i["explicit"] else "o", str(i["tempo"]), str(i["energy"]), str(i["danceability"])) for i in data)

    table = Table(*columns)
    for row in rows:
      table.add_row(*row) 
      
    self.query_one("#results", Static).update(table)


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
