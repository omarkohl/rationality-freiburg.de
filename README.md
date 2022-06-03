# rationality-freiburg.de

Static website made with [Hugo](https://gohugo.io/).

Visit [www.rationality-freiburg.de](https://www.rationality-freiburg.de)

# Contributing

## Easy way

The simplest way of contributing (e.g. if you found a mistake in one of the
posts) is to simply edit the .md (MarkDown) documents you can find under the
content/en/ directory. Then simply send a pull request.

To create a new post you can copy an existing document or folder (basically
only needed if the post contains images) and adapt as needed.

To create or update German translations you can use
[DeepL](https://www.deepl.com/translator) and modify/create corresponding files
under content/de/ .

## Using hugo

This website is created using the static site generator
[Hugo](https://gohugo.io/). If you want to contribute frequently or want to
preview your post you can [install
Hugo](https://gohugo.io/getting-started/installing/) and then:

```bash
hugo new posts/some-examples.md
# edit content/posts/en/some-example.md
# optionally edit content/posts/de/some-example.md for the German translation
hugo server -D
```

Open http://localhost:1313 in a browser and check your post.

[Learn more about Hugo](https://gohugo.io/getting-started/quick-start/).
