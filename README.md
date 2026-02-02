<div align=center>

![Glyph app screenshot](./data/screenshots/banner.png)

<img src="./data/icons/hicolor/scalable/apps/io.github.shonebinu.Glyph.svg" alt="Glyph Logo" width="128" >

# Glyph

**Install fonts**

![Flathub Downloads](https://img.shields.io/flathub/downloads/io.github.shonebinu.Glyph?style=for-the-badge)
![Flathub Version](https://img.shields.io/flathub/v/io.github.shonebinu.Glyph?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/shonebinu/Glyph?style=for-the-badge&color=yellow)

</div>

## Description

Glyph is an app for installing fonts from [Google Fonts Github Repo](https://github.com/google/fonts) written in Python, using GTK4 and Libadwaita. It lets you search through thousands of available fonts and install them into your system in original quality.

## Features

- Preview fonts without internet or installation.
- Search through thousands of fonts in various categories such as sans, mono etc.
- Install the latest font to your system.
- View the details of fonts such as the designer, license, files etc.
- Fonts fetched from Google Fonts Github repo with original quality.

## Install

<a href='https://flathub.org/apps/io.github.shonebinu.Glyph'>
    <img width='240' alt='Get Brief on Flathub' src='https://flathub.org/api/badge?svg&locale=en '/>
</a>

## Development

You can clone this project and run it using [Gnome Builder](https://apps.gnome.org/Builder/). The Python libraries used in this project are defined inside [requirements.txt](./requirements.txt), which you may install if you want editor completions.

**Note to myself**

`"--filesystem=xdg-data/fonts:create"` will throw a linter error when publishing to Flathub, but at the same time, it is needed for proper development using GNOME builder/Foundry. (with the below permission alone, Pango/GTK isn't reading fonts from user fonts directory and is not able to write to the same for whatever reason while running it)

Hence, use `"--filesystem=~/.local/share/fonts:create"` when publishing. This is working for published/built apps(not running from Gnome builder/foundry) but not for development.

If someone could point out how to resolve this cleanly without any Flathub exceptions, help me :).

## Credits

The entirety of the data used in this project is from [Google Fonts Github Repo](https://github.com/google/fonts).
