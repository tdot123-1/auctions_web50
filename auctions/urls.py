from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create"),
    path("listing/<int:listing_id>", views.listing_page, name="listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("update_watchlist", views.update_watchlist, name="update"),
    path("close_auction", views.close_auction, name="close"),
    path("categories", views.all_categories, name="categories"),
    path("categories/<str:name>/<str:value>", views.category, name="category"),
    path("my_auctions", views.my_auctions, name="my_auctions"),
    path("auctions_won", views.auctions_won, name="auctions_won"),
    path("search", views.search, name="search")
]
