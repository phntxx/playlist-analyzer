# playlist-analyzer

## usage

i assume you already did set up a project with spotify [here](https://developer.spotify.com/dashboard/applications) and have your client id, client secreat and redirect uri set (redirect uri set to e.g. "http://localhost:8080/")

1. `pip install -r requirements.txt`

2. copy `config.template.yml` to `config.yml`: `cp config.yml`

3. adjust `config.yml` to your needs

4. `python3 main.py`
