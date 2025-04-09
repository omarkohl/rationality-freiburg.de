# rationality-freiburg.de

Static website made with [Hugo](https://gohugo.io/).

Visit [www.rationality-freiburg.de](https://www.rationality-freiburg.de)


# Contributing

## Easy way

The simplest way of contributing (e.g. if you found a mistake in one of the
posts) is to simply edit the .md (MarkDown) documents you can find under the
`website/content/` directory. Then simply send a pull request.

To create a new post you can copy an existing document or folder (basically
only needed if the post contains images) and adapt as needed.

To create or update German translations you can use
[DeepL](https://www.deepl.com/translator) and modify/create corresponding files
under `website/content/de/` .


## Using hugo

This website is created using the static site generator
[Hugo](https://gohugo.io/). If you want to contribute frequently or want to
preview your post you can [install
Hugo](https://gohugo.io/getting-started/installing/) and then:

```bash
cd website
hugo new posts/some-examples.md
# edit content/posts/some-example.md
# optionally edit content/posts/some-example.de.md for the German translation
hugo server -D
```

Open http://localhost:1313 in a browser and check your post.

[Learn more about Hugo](https://gohugo.io/getting-started/quick-start/).


# Adding Events

```bash
cd website
NAME=2025-03-28-cognitive-biases
hugo new events/${NAME}/_index.md
vim content/events/${NAME}/_index.md
cp ~/Desktop/cover.png content/events/${NAME}/cover.png
convert -resize 512x512 content/events/${NAME}/cover.png content/events/${NAME}/cover.png
cp content/events/${NAME}/_index.md content/events/${NAME}/_index.de.md
vim content/events/${NAME}/_index*.md
jj commit -m "Add event ${NAME}"
```

To edit an existing event (e.g. because initially there was no theme).

```bash
cd website
git mv content/events/2023-02-17-meetup/ content/events/2023-02-17-exercising/
vim content/events/2023-02-17-exercising/_index*.md
```

Add an `aliases` section in each case:

```yaml
aliases:
  - /events/2023-02-17-meetup/
```

```yaml
aliases:
  - /de/termine/2023-02-17-meetup/
```

Edit the title, description, slug and content in each case.
