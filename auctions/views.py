from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import User, Listing, Comment, Bid
from .forms import ListingForm


# display all active listings
def index(request):

    listing = Listing.objects.filter(status="active")

    return render(request, "auctions/index.html", {"listings": listing})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    

# create new listing
@login_required(login_url="login")
def create_listing(request):
    if request.method == "POST":
        # get form information
        form = ListingForm(request.POST)
        if form.is_valid():
            # create new listing object without saving initially
            new_listing = form.save(commit=False)

            # capitalize title
            new_listing.title = new_listing.title.capitalize()

            # set seller to current user, set current price to starting bid
            new_listing.seller = request.user
            new_listing.current_price = new_listing.starting_bid

            # save and redirect back to index
            new_listing.save()
            return HttpResponseRedirect(reverse("index"))
        
    else:
        form = ListingForm()
    
    return render(request, "auctions/create_listing.html", {"form": form})


# view for specific listing
@login_required(login_url="login")
def listing_page(request, listing_id):

    # get listing object by id, get all bids on object, set error message to None
    item_listing = Listing.objects.get(pk=listing_id)
    message = None
    bids = Bid.objects.filter(listing=item_listing)

    if request.method == "POST":
        if "new-comment" in request.POST:

            # if comment is made, create new Comment object
            comment_content = request.POST.get("new-comment")
            comment_author = request.user
            new_comment = Comment.objects.create(
                author=comment_author,
                listing=item_listing,
                content=comment_content
            )
        
        elif "reply-comment" in request.POST:

            # if reply is made, create new Comment object
            comment_content = request.POST.get("reply-comment")
            comment_author = request.user
            comment_on_id = int(request.POST.get("commented-on"))
            parent_comment = Comment.objects.get(pk=comment_on_id)
            new_comment = Comment.objects.create(
                author=comment_author,
                listing=item_listing,
                content=comment_content,
                is_reply=parent_comment
            )

        elif "new-bid" in request.POST:

            # if bid is made on listing, check if bid is high enough
            bid_amount = float(request.POST.get("new-bid"))
            if bid_amount <= item_listing.current_price:
                message = {
                    "content": "Bid must be higher than current price.",
                    "category": "warning"
                }
            else:

                # if bid is higher than current price, create new Bid object
                message = {
                    "content": "Bid succesful!",
                    "category": "success"
                }
                bid_author = request.user
                new_bid = Bid.objects.create(
                    amount=bid_amount,
                    bidder=bid_author,
                    listing=item_listing,
                )
                # update current price and winner to Listing object
                item_listing.current_price = bid_amount
                item_listing.winner = bid_author
                item_listing.save()
                
    # get all comments on Listing object that are not replies
    comments = Comment.objects.filter(listing=listing_id, is_reply__isnull=True)
    
    return render(request, "auctions/listing_page.html", {
        "listing": item_listing,
        "comments": comments,
        "message": message,
        "bids": bids
        })


# watchlist
@login_required(login_url="login")
def watchlist(request):
    # remove items from watchlist 
    if request.method == "POST":
        user = request.user
        listing_id = int(request.POST.get("remove"))
        listing = Listing.objects.get(pk=listing_id)
        if listing in user.watchlist.all():
            user.watchlist.remove(listing)

    return render(request, "auctions/watchlist.html", {})


# remove/add items from watchlist on pages other than watchlist page
@login_required(login_url="login")
def update_watchlist(request):
    if request.method == "POST":
        user = request.user
        if "remove" in request.POST:
            # get listing id
            listing_id = int(request.POST.get("remove"))
            listing = Listing.objects.get(pk=listing_id)
            # remove from 'watchlist'
            if listing in user.watchlist.all():
                user.watchlist.remove(listing)

        elif "add" in request.POST:
            # get listing id
            listing_id = int(request.POST.get("add"))
            listing = Listing.objects.get(pk=listing_id)
            # add to watchlist
            if listing not in user.watchlist.all():
                user.watchlist.add(listing)

    return HttpResponseRedirect(reverse("index"))


# close auction
@login_required(login_url="login")
def close_auction(request):
    if request.method == "POST":
        # get listing object by id, update status
        listing_id = request.POST.get("close")
        listing = Listing.objects.get(pk=listing_id)
        if listing.status == "active":
            listing.status = "ended"
            listing.save()
        
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
    
    return HttpResponseRedirect(reverse("index"))


# display all listing categories
def all_categories(request):
    categories = []
    for choice in Listing.CATEGORY_CHOICES:
        category_name = choice[1]
        category_value = choice[0]
        # show amount of objects per category
        count = Listing.objects.filter(category=category_value).count()
        categories.append({"name": category_name, "count": count, "value": category_value})

    return render(request, "auctions/all_categories.html", {"categories": categories})


# display all listings in specified category
def category(request, name, value):
    listings = Listing.objects.filter(category=value)
    
    return render(request, "auctions/category.html", {
        "listings": listings,
        "category": name
        })


# display all listings created by user
@login_required(login_url="login")
def my_auctions(request):
    user = request.user

    listings = Listing.objects.filter(seller=user)

    return render(request, "auctions/my_auctions.html", {
        "listings": listings
    })


# display all listings won by user/ listings where user currently has highest bid
@login_required(login_url="login")
def auctions_won(request):
    user = request.user

    listings = Listing.objects.filter(winner=user)

    return render(request, "auctions/auctions_won.html", {
        "listings": listings
    })


# search for listings
def search(request):
    query = request.GET.get("q")

    if query:
        query = str(query)
        listings = Listing.objects.filter(Q(title__icontains=query))

        return render(request, "auctions/search_results.html", {
            "listings": listings,
            "query": query
        })
    
    return HttpResponseRedirect(reverse("index"))

