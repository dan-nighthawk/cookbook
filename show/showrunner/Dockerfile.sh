# Showrunner engine — shell port (bash + curl + jq). Build from the REPO ROOT:
#   docker build -f marketing/showrunner/Dockerfile.sh -t yakyak/showrunner-sh .
#
# Pin the base image by digest in CI and tag by git SHA for reproducibility.
#
# Run:
#   docker run --rm -e YAKYAK_PAT \
#     -v "$PWD/marketing/Horoscopes/stories:/app/marketing/Horoscopes/stories" \
#     yakyak/showrunner-sh --show marketing/Horoscopes --post --yes
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash curl jq ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY marketing/ marketing/
RUN mkdir -p /app/e2e && touch /app/e2e/.env.bb \
    && chmod +x marketing/showrunner/upload_to_yakyak.sh marketing/showrunner/prepare.sh

ENTRYPOINT ["marketing/showrunner/upload_to_yakyak.sh"]
