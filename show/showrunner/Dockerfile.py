# Showrunner engine — Python port. Build from the REPO ROOT so the COPY paths
# resolve:  docker build -f marketing/showrunner/Dockerfile.py -t yakyak/showrunner-py .
#
# "Controlled" knobs: pin the base image by digest in CI (FROM python:3.12-slim@sha256:...)
# and tag the image by git SHA. requirements.txt already pins yakyak-sdk.
#
# Run (PAT via env; stories + secret mounted, never baked):
#   docker run --rm -e YAKYAK_PAT \
#     -v "$PWD/marketing/Horoscopes/stories:/app/marketing/Horoscopes/stories" \
#     yakyak/showrunner-py --show marketing/Horoscopes --post --yes
FROM python:3.12-slim

WORKDIR /app
COPY marketing/showrunner/requirements.txt marketing/showrunner/requirements.txt
RUN pip install --no-cache-dir -r marketing/showrunner/requirements.txt

# Engine + all show configs (campaign ids, prompts, compute.py). Stories are
# generated/mounted at runtime, not relied upon from the image.
COPY marketing/ marketing/

# The engines require e2e/.env.bb to *exist*; the PAT itself comes via -e at run
# time so it never lands in an image layer.
RUN mkdir -p /app/e2e && touch /app/e2e/.env.bb

ENTRYPOINT ["python", "marketing/showrunner/upload_to_yakyak.py"]
