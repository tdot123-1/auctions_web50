from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    watchlist = models.ManyToManyField("Listing", related_name="watched_by", blank=True)

    def __str__(self):
        return f"{self.username}"


# auction listings
class Listing(models.Model):

    CATEGORY_CHOICES = [
        ("home", "Home"),
        ("gardening", "Gardening"),
        ("fashion", "Fashion"),
        ("electronics", "Electronics"),
        ("toys", "Toys"),
        ("books", "Books"),
        ("cosmetics", "Cosmetics"),
        ("other", "Other")
    ]

    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=64, choices=CATEGORY_CHOICES)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="auctions_created")
    winner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="auctions_won")
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('ended', 'Ended')], default='active')

    def __str__(self):
        return f"{self.pk}: {self.title}"

# bids
class Bid(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids_made")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="listing_bids")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pk}: {self.amount} by {self.bidder} on {self.listing}"

# comments on auction listings
class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments_made")
    content = models.TextField()
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="listing_comments")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_reply = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")

    def __str__(self):
        return f"{self.pk}: {self.author}"