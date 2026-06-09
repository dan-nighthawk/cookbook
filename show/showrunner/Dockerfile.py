# Showrunner engine — Python port. Build with ./show as the context so the COPY
# paths resolve:  docker build -f show/showrunner/Dockerfile.py -t yakyak/showrunner-py show
#
# "Controlled" knobs: pin the base image by digest in CI (FROM python:3.12-slim@sha256:...)
# and tag the image by version. requirements.txt already pins yakyak-sdk.
#
# Run (PAT via env; stories + secret mounted, never baked):
#   docker run --rm -e YAKYAK_PAT \
#     -v "$PWD/show/Horoscopes/stories:/app/Horoscopes/stories" \
#     yakyak/showrunner-py --show Horoscopes --post --yes
FROM python:3.12-slim

WORKDIR /app
COPY showrunner/requirements.txt showrunner/requirements.txt
RUN pip install --no-cache-dir -r showrunner/requirements.txt

# Engine + all show configs (campaign ids, prompts, compute.py). Stories are
# generated/mounted at runtime, not relied upon from the image.
COPY . .

# The engines require e2e/.env.bb to *exist*; the PAT itself comes via -e at run
# time so it never lands in an image layer.
RUN mkdir -p /app/e2e && touch /app/e2e/.env.bb

ENTRYPOINT ["python", "showrunner/upload_to_yakyak.py"]
