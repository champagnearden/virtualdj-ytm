# virtualdj-ytmMake sure to have [ffmpeg](https://www.ffmpeg.org/download.html "Download ffmpeg") installed:

1. ```bash
   ffmpeg -version
   ```
2. Install the dependencies using the [vcpkg](https://vcpkg.io/en/ "vcpkg home page") install command:
   ```bash
   vcpkg install
   ```
3. Install [python](https://www.python.org/downloads/ "Download python") package:
   1. Check if you have python installed with:

      ```bash
      python --version
      ```
   2. Check if you have `pip` installed and up to date:

      ```bash
      pip --version && pip install --upgrade pip
      ```
   3. Install the package `yt-dlp`:

      ```bash
      pip install yt-dlp
      ```

# Main objective

The main goal of virtualdj-ytm is to make possible the action to search song on youtube directly with youtube music results, download the song in `.m4a` format and then make it available for your mix !

# Future

Features in coming:

* Use your google account to get personnalized results
* Stream musics without downloading them (warning ads for non-premium users)
* Choose destination directory
