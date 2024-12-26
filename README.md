# osu-about-me-graph

A command-line tool for generating graph networks based on the "About Me" pages of [osu!](https://osu.ppy.sh) players.

![](media/example-500.png)

## Getting Started
To pull data from the osu!API, you will need a registered [osu! OAuth client](https://osu.ppy.sh/home/account/edit). Click **'New OAuth Application +'**, then enter a name and hit **'Register application'**. Take note of your client ID and secret.

1. Navigate to the project root directory and setup environment variables:
    - Bash:
        - `printf "OSU_API_CLIENT_ID=[your client ID]\nOSU_API_CLIENT_SECRET=[your client secret]" > .env`
    - PowerShell:
        - ``Set-Content -Path .env -Value "OSU_API_CLIENT_ID=[your client ID]`nOSU_API_CLIENT_SECRET=[your client secret]" -Encoding utf8``

2. (Optional) Set up virtual environment:
    - Bash:
        - `python -m venv venv`
        - `source venv/bin/activate`
    - PowerShell:
        - `python -m venv venv`
        - `./venv/Scripts/Activate`

3. Install dependencies:
    - `pip install ossapi networkx matplotlib asyncio aiohttp python-dotenv scipy numpy pillow`

To use the tool, run `python src/main.py`. This will generate a PNG image of the graph. To generate and view an interactive HTML/JS version:
- Run `python src/main.py --save-json --no-graph <optional extra flags>`
- Start a local development server (e.g. `npx http-server` or `python -m http.server`)
- Open `localhost:<port>/html/user_network.html` in a browser

## Features
For a list of all customization flags, run `python src/main.py -h`.
- Gamemode selection (std, taiko, mania, catch) and user rank selection (i.e. build a graph for users ranked #324 - #727)
- Rich customization support for graph generation including:
    - Rank-range selection, clustering strength, and connection strength (i.e. build a graph where users with ranks #1-#100, #101-#200, etc. are tightly packed in clusters).
    - Node centralization parameters (i.e. group users around the center where more-mentioned ones are pulled closer/farther)
    - All of the other good stuff - edge curvature/width, image size/DPI, legend/label/node customization, and more!
- Supports savefiles, so that you don't have to re-pull from the API on every run.
- Takes all previous usernames into account; i.e. if players reference 'ryuk' in their profile but he renames to 'connor mcdavid', mentions will still be tallied.
- Automatically resolves rename conflicts; i.e. if players reference 'shigetora' in their profile but he renames to 'chocomint' and someone else takes the name 'shigetora', mentions will be correctly attributed to 'chocomint'.
- Generates a configurable 'possible false-positives report' which demarcates usernames that may incorrectly be receiving mention tallies because of their common use in profile pages ('hello', 'wooting', 'hddt', etc.). These usernames can then subsequently be ignored by their addition to a CSV file.
- PNG format (using networkX) and interactive HTML/JS format (using cytoscape.js)

## Contributing
If you find any bugs or want to request a feature, feel free to open an [issue](https://github.com/mbalsdon/osu-about-me-graph/issues). If you want to make changes, feel free to open a PR. For direct contact, my DMs are open on Discord @spreadnuts.
