"""Pixel icon for the exploration entry on the top bar."""
from scripts.menu_icons import render_menu_icon


def render_explore_icon(size=20):
    """A compass in the same dark, beveled tile as the navigation icons."""
    return render_menu_icon("Explore", size)
