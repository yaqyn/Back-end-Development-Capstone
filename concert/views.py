import os

import requests as req
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from concert.forms import LoginForm, SignUpForm
from concert.models import Concert, ConcertAttending

SONG_URL = os.environ.get("SONG_URL", "").rstrip("/")
PHOTO_URL = os.environ.get("PHOTO_URL", "").rstrip("/")

DEMO_SONGS = [
    {
        "id": 1,
        "title": "duis faucibus accumsan odio curabitur convallis",
        "lyrics": (
            "Morbi non lectus. Aliquam sit amet diam in magna bibendum "
            "imperdiet. Nullam orci pede, venenatis non, sodales sed, "
            "tincidunt eu, felis."
        ),
    }
]

DEMO_PHOTOS = [
    {
        "id": 1,
        "pic_url": "https://dummyimage.com/136x100.png/5fa2dd/ffffff",
        "event_country": "United States",
        "event_state": "District of Columbia",
        "event_city": "Washington",
        "event_date": "11/16/2022",
    }
]


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        return render(request, "signup.html", {"form": form})

    return render(request, "signup.html", {"form": SignUpForm()})


def index(request):
    return render(request, "index.html")


def _service_get(url):
    """Fetch a JSON payload from a microservice, with a short timeout."""
    response = req.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def songs(request):
    song_data = DEMO_SONGS
    if SONG_URL:
        try:
            payload = _service_get(f"{SONG_URL}/song")
            song_data = payload.get("songs", [])
        except (req.RequestException, ValueError):
            song_data = DEMO_SONGS

    return render(request, "songs.html", {"songs": song_data})


def photos(request):
    photo_data = DEMO_PHOTOS
    if PHOTO_URL:
        try:
            photo_data = _service_get(f"{PHOTO_URL}/picture")
        except (req.RequestException, ValueError):
            photo_data = DEMO_PHOTOS

    return render(request, "photos.html", {"photos": photo_data})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                login(request, user)
                return HttpResponseRedirect(reverse("index"))
        except User.DoesNotExist:
            pass

        return render(
            request,
            "login.html",
            {"form": LoginForm, "message": "Invalid username or password"},
        )

    return render(request, "login.html", {"form": LoginForm})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def concerts(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    concert_rows = []
    for concert in Concert.objects.all().order_by("date", "concert_name"):
        attendance = concert.attendee.filter(user=request.user).first()
        concert_rows.append(
            {
                "concert": concert,
                "status": attendance.attending if attendance else "-",
            }
        )

    return render(request, "concerts.html", {"concerts": concert_rows})


def concert_detail(request, id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    concert = get_object_or_404(Concert, pk=id)
    attendance = concert.attendee.filter(user=request.user).first()
    status = attendance.attending if attendance else "-"
    return render(
        request,
        "concert_detail.html",
        {
            "concert_details": concert,
            "status": status,
            "attending_choices": ConcertAttending.AttendingChoices.choices,
        },
    )


@login_required(login_url="login")
@require_POST
def concert_attendee(request):
    concert = get_object_or_404(Concert, pk=request.POST.get("concert_id"))
    attendee_status = request.POST.get("attendee_choice")
    valid_statuses = {
        choice for choice, _label in ConcertAttending.AttendingChoices.choices
    }
    if attendee_status not in valid_statuses:
        return HttpResponseBadRequest("Invalid RSVP choice.")

    ConcertAttending.objects.update_or_create(
        concert=concert,
        user=request.user,
        defaults={"attending": attendee_status},
    )

    return HttpResponseRedirect(reverse("concerts"))
