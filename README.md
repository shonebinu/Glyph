# Glyph

Google fonts installer for Linux

## Plan

GTK4 Libadwaita Python app. Flatpak only. Fonts can be installed to `~/.local/share/fonts`.

For all the approaches, we will have a Github runner that runs through google-fonts github repo and parses fonts metadata to a single json file which has all the available fonts and links to its full ttf files. Updated every 24h.

### Aproach 1

My initial idea.

A sidebar which lists the categories (All fonts, Serif, Sans etc). The right side, list view showing the available fonts in the categories with preview text. We will show the preview text by fetching a batch of minimal font subset from google fonts CSS api with text param and add the font to Pango `https://fonts.googleapis.com/css2?family=Inter&text=The%20quick%20brown%20fox`.

Fetching CSS, then parsing it for font file is extra headache, i could maybe modify my github action to generate a subset of font (for specific characters) and append it into my the json file.

Variations of this approach is how its done in google fonts, font source, bunny fonts homepages. Good and fast in web/browser scenario, but really slow and bad for a native app(too much overhead).

Bad UX, Pango errors probably due to font subsets. Network latency. Batch loading fonts upon scrolling doesn't feel good.

Could bundle latin 400(or some text subset) subsets of every font w/ app, but app size would be huge. If user change preview text to something not within latin 400, need to fetch again. Simpler method is still using gfonts CSS api with text param.

Loading 10s and 100s of fonts to Pango seem to break sometimes. This is risky. And not as smooth as just adding font face property in browser.

### Approach 2

Approach of this app: https://flathub.org/en/apps/org.gustavoperedo.FontDownloader
This app seems currently unmaintained.

Sidebar containing all the font family names. Upon clicking one, right side webview shows up with font preview. Can easily add font preview with just a google stylesheets link.

Easiest of all. but will look out of place. and will be heavy

### Approach 3

With GH actions, also create svg previews of all fonts. Show it in listview, upon clicking an item open details page,where we download the full files. On Details page we use Pango for rendering. It would be better than both the cases above. We could update the action every week. also bundle the file with app to reduce the latency even more. could update the list in background. This would have less overhead.
This is way better than working with 100s of fonts with Pango. also not so much resource intensive in the user side.

https://github.com/alexmyczko/fnt/

this app also saves svg
