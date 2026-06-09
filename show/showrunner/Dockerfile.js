# Showrunner engine — Node port. Build with ./show as the context:
#   docker build -f show/showrunner/Dockerfile.js -t yakyak/showrunner-js show
#
# Pin the base image by digest in CI and tag by version for reproducibility.
#
# Run:
#   docker run --rm -e YAKYAK_PAT \
#     -v "$PWD/show/Horoscopes/stories:/app/Horoscopes/stories" \
#     yakyak/showrunner-js --show Horoscopes --post --yes
FROM node:22-slim

WORKDIR /app
COPY . .
# Install prod deps fresh in the engine dir (drop any host node_modules first so a
# local checkout can't leak in). package-lock.json pins yakyak-sdk.
RUN rm -rf showrunner/node_modules \
    && cd showrunner && npm ci --omit=dev

RUN mkdir -p /app/e2e && touch /app/e2e/.env.bb

ENTRYPOINT ["node", "showrunner/upload_to_yakyak.js"]
