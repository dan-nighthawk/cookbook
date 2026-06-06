# Run the Python version of any course lesson, e.g.:  make 05-byo-image
#   JS equivalent:    npm run 05-byo-image
#   bash equivalent:  bash 05-byo-image/byo-image.sh
# Override the interpreter if needed:  make PYTHON=python3 05-byo-image
PYTHON ?= python

.PHONY: help install \
        01-signup 02-hello-world 03-new-campaign 04-edit-movie \
        05-byo-image 06-intro-clip 07-soundtrack 08-social-post

help:
	@echo "Run a lesson's Python script, e.g.:  make 05-byo-image"
	@echo "Lessons: 01-signup 02-hello-world 03-new-campaign 04-edit-movie \\"
	@echo "         05-byo-image 06-intro-clip 07-soundtrack 08-social-post"
	@echo "First time:  make install   (pip install -r requirements.txt)"

install: ; $(PYTHON) -m pip install -r requirements.txt

01-signup:       ; $(PYTHON) 01-signup/signup.py
02-hello-world:  ; $(PYTHON) 02-hello-world/hello.py
03-new-campaign: ; $(PYTHON) 03-new-campaign/new-campaign.py
04-edit-movie:   ; $(PYTHON) 04-edit-movie/edit-movie.py
05-byo-image:    ; $(PYTHON) 05-byo-image/byo-image.py
06-intro-clip:   ; $(PYTHON) 06-intro-clip/intro-clip.py
07-soundtrack:   ; $(PYTHON) 07-soundtrack/soundtrack.py
08-social-post:  ; $(PYTHON) 08-social-post/social-post.py
