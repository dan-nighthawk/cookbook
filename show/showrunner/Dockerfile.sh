# Showrunner engine — shell port (bash + curl + jq). Build with ./show as the context:
#   docker build -f show/showrunner/Dockerfile.sh -t yakyak/showrunner-sh show
#
# Pin the base image by digest in CI and tag by version for reproducibility.
#
# Run:
#   docker run --rm -e YAKYAK_PAT \
#     -v "$PWD/show/Horoscopes/stories:/app/Horoscopes/stories" \
#     yakyak/showrunner-sh --show Horoscopes --post --yes
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash curl jq ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN mkdir -p /app/e2e && touch /app/e2e/.env.bb \
    && chmod +x showrunner/upload_to_yakyak.sh showrunner/prepare.sh

ENTRYPOINT ["showrunner/upload_to_yakyak.sh"]
