from enum import Enum

class AnimeType(str, Enum):
    TV = "TV"
    Movie = "Movie"
    OVA = "OVA"
    ONA = "ONA"
    Special = "Special"


class AnimeStatus(str, Enum):
    Airing = "Airing"
    Finished = "Finished"
    Upcoming = "Upcoming"