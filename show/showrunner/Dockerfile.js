# Showrunner engine — Node port. Build from the REPO ROOT:
#   docker build -f marketing/showrunner/Dockerfile.js -t yakyak/showrunner-js .
#
# Pin the base image by digest in CI and tag by git SHA for reproducibility.
#
# Run:
#   docker run --rm -e YAKYAK_PAT \
#     -v "$PWD/marketing/Horoscopes/stories:/app/marketing/Horoscopes/stories" \
#     yakyak/showrunner-js --show marketing/Horoscopes --post --yes
FROM node:22-slim

WORKDIR /app
COPY marketing/ marketing/
# Install prod deps fresh in the engine dir (drop any host node_modules first so a
# local checkout can't leak in). package-lock.json pins yakyak-sdk.
RUN rm -rf marketing/showrunner/node_modules \
    && cd marketing/showrunner && npm ci --omit=dev

RUN mkdir -p /app/e2e && touch /app/e2e/.env.bb

ENTRYPOINT ["node", "marketing/showrunner/upload_to_yakyak.js"]
