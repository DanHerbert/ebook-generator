# Ebook Generator

Some code to take a big chunk of HTML and split it into chapters in an ePub file.

Chapters are assumed to be delimited with either `<p>chapter</p>` or `<p><strong>chapter</strong></p>`.

Used for one of my Patreon subscriptions to a book author which does not provide an ePub file but posts their work as HTML when published on Patreon.

## Setup and Requirements

I have only tested this app on Linux, but it should work on MacOS as well. Windows may be possible, but could require setting up WSL to use. Try at your own risk.

This script requires Python to be installed on your system, as well as 2 other apps to be installed before running: "`rsvg-convert`" and "`ImageMagick`".

`rsvg-convert` is available on most Linux/MacOS package managers under a few different names:

* [`librsvg`](https://formulae.brew.sh/formula/librsvg) on MacOS/Linux Homebrew
* [`librsvg2-bin`](https://packages.debian.org/stable/librsvg2-bin) on Debian-based distributions (Ubuntu, Mint, etc)
* [`librsvg2-tools`](https://packages.fedoraproject.org/pkgs/librsvg2/librsvg2-tools/) on Red Hat-based distros
* [`librsvg`](https://archlinux.org/packages/extra/x86_64/librsvg/) on Arch-based distros (Manjaro, SteamOS, etc)


[ImageMagick](https://imagemagick.org/script/download.php) is available in most package managers as simply `imagemagick`.

## Usage

In the `/inputs/` folder, copy `metadata.example.yaml` as `metadata.yaml` in the same folder, filling in the details for each field. Copy `content.example.html` as `content.html` in the same folder, filling in the HTML code for the ebook you want to generate.

Depending on your machine, once those files are ready you can simply run `./src/generate_ebook.py` from a terminal to generate the output. You may need to set up a Python venv by running the following commands:

```sh
python3 -m venv venv
source venv/bin/activate
pip install .
```

Once those commands finish you should be able to re-run the `./src/generate_ebook.py` script.

When the script is finished, the file `book.epub` will be in the project's root.
