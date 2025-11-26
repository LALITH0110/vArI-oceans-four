"""
North Atlantic city coordinates for interactive scenarios.

Provides a curated list of 18 cities on both sides of the Atlantic
with known lon/lat coordinates for particle release scenarios.
"""

# City coordinates: {name: (lon, lat)}
CITIES = {
    # North America - East Coast
    "New York": (-74.0, 40.6),
    "Boston": (-70.9, 42.3),
    "Miami": (-80.2, 25.8),
    "Chesapeake Bay": (-76.3, 38.8),
    "Halifax": (-63.6, 44.6),

    # Europe - West Coast
    "Lisbon": (-9.14, 38.72),
    "Porto": (-8.62, 41.15),
    "Vigo": (-8.72, 42.23),
    "Bilbao": (-3.00, 43.26),
    "Brest": (-4.49, 48.39),
    "Le Havre": (0.10, 49.49),
    "London (Thames)": (0.00, 51.50),
    "Rotterdam": (4.48, 51.92),
    "Hamburg": (9.99, 53.55),
    "Dublin": (-6.26, 53.35),
    "Glasgow": (-4.25, 55.86),

    # Atlantic Islands
    "Azores": (-28.0, 38.6),
    "Canaries": (-16.3, 28.3),
    "Madeira": (-16.9, 32.7),
}


def get_city_list():
    """Get sorted list of city names."""
    return sorted(CITIES.keys())


def get_city_coords(city_name):
    """
    Get coordinates for a city.

    Parameters
    ----------
    city_name : str
        City name (case-insensitive)

    Returns
    -------
    lon : float
        Longitude in degrees
    lat : float
        Latitude in degrees

    Raises
    ------
    ValueError
        If city not found
    """
    # Case-insensitive lookup
    for name, (lon, lat) in CITIES.items():
        if name.lower() == city_name.lower():
            return lon, lat

    raise ValueError(f"City '{city_name}' not found. Available: {get_city_list()}")


def fuzzy_match_city(query, threshold=0.6):
    """
    Find cities matching a query string (fuzzy matching).

    Parameters
    ----------
    query : str
        Search query
    threshold : float
        Minimum match score (0-1)

    Returns
    -------
    matches : list of str
        Matching city names, sorted by relevance
    """
    from difflib import SequenceMatcher

    query = query.lower()
    matches = []

    for city_name in CITIES.keys():
        # Check if query is substring
        if query in city_name.lower():
            matches.append((city_name, 1.0))
            continue

        # Compute similarity score
        score = SequenceMatcher(None, query, city_name.lower()).ratio()
        if score >= threshold:
            matches.append((city_name, score))

    # Sort by score descending
    matches.sort(key=lambda x: -x[1])

    return [name for name, score in matches]


def city_to_slug(city_name):
    """
    Convert city name to filesystem-safe slug.

    Parameters
    ----------
    city_name : str
        City name

    Returns
    -------
    slug : str
        Filesystem-safe slug
    """
    import re
    slug = city_name.lower()
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = slug.strip('_')
    return slug


def get_recommended_season(city_name):
    """
    Get recommended release season for a city (for fake RL story).

    This is a simple heuristic for the storyboard:
    - Northern latitudes (>45N): prefer winter (stronger Gulf Stream)
    - Southern latitudes (<35N): prefer summer (subtropical gyre)
    - Mid-latitudes: prefer winter

    Parameters
    ----------
    city_name : str
        City name

    Returns
    -------
    season : str
        "winter" or "summer"
    reason : str
        Short explanation
    """
    lon, lat = get_city_coords(city_name)

    if lat > 45:
        return "winter", "strong Gulf Stream transport"
    elif lat < 35:
        return "summer", "subtropical gyre retention"
    else:
        return "winter", "optimal eastward drift"


if __name__ == '__main__':
    print("North Atlantic Cities Database")
    print("=" * 60)
    print(f"Total cities: {len(CITIES)}")
    print()

    print("City list:")
    for i, city in enumerate(get_city_list(), 1):
        lon, lat = CITIES[city]
        season, reason = get_recommended_season(city)
        print(f"  {i:2d}. {city:20s} ({lon:7.2f}, {lat:6.2f}) -> {season:6s} ({reason})")

    print()
    print("Testing fuzzy match:")
    for query in ["new", "lond", "azor", "ham"]:
        matches = fuzzy_match_city(query)
        print(f"  '{query}' -> {matches}")

    print()
    print("Testing slugs:")
    for city in ["New York", "London (Thames)", "Le Havre"]:
        print(f"  '{city}' -> '{city_to_slug(city)}'")
