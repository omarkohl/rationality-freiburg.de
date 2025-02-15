# Slides

```bash
docker pull marpteam/marp-cli
```

`cd` into current directory, then:

```bash
# Convert slide deck into HTML
docker run --rm -v $PWD:/home/marp/app/ -e LANG=$LANG -e MARP_USER="$(id -u):$(id -g)" marpteam/marp-cli slides.md -o temp.html

# Convert slide deck into PDF (using Chromium in Docker)
docker run --rm --init -v $PWD:/home/marp/app/ -e LANG=$LANG -e MARP_USER="$(id -u):$(id -g)" marpteam/marp-cli slides.md --pdf --allow-local-files -o temp.pdf

# Watch mode
docker run --rm --init -v $PWD:/home/marp/app/ -e LANG=$LANG -e MARP_USER="$(id -u):$(id -g)" -p 37717:37717 marpteam/marp-cli -w slides.md -o temp.html

# Server mode (Serve current directory in http://localhost:8080/)
docker run --rm --init -v $PWD:/home/marp/app -e LANG=$LANG -e MARP_USER="$(id -u):$(id -g)" -p 8080:8080 -p 37717:37717 marpteam/marp-cli --html -s . 
```

## Notes

https://chris-ayers.com/2023/03/31/customizing-marp

