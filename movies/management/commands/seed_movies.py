"""
Management command to seed the database with sample movies.
Run: python manage.py seed_movies
"""
from django.core.management.base import BaseCommand
from movies.models import Movie, Genre


GENRES_DATA = [
    "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Horror", "Mystery",
    "Romance", "Sci-Fi", "Thriller", "Western"
]

MOVIES_DATA = [
    {
        "title": "The Shawshank Redemption",
        "year": 1994,
        "director": "Frank Darabont",
        "genres": ["Drama"],
        "cast": "Tim Robbins, Morgan Freeman, Bob Gunton",
        "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
        "imdb_rating": 9.3,
        "runtime_minutes": 142,
    },
    {
        "title": "The Godfather",
        "year": 1972,
        "director": "Francis Ford Coppola",
        "genres": ["Crime", "Drama"],
        "cast": "Marlon Brando, Al Pacino, James Caan",
        "description": "The aging patriarch of an organized crime dynasty transfers control to his reluctant son.",
        "imdb_rating": 9.2,
        "runtime_minutes": 175,
    },
    {
        "title": "The Dark Knight",
        "year": 2008,
        "director": "Christopher Nolan",
        "genres": ["Action", "Crime", "Drama"],
        "cast": "Christian Bale, Heath Ledger, Aaron Eckhart",
        "description": "Batman raises the stakes in his war on crime. With the help of allies he fights the chaos unleashed by the Joker.",
        "imdb_rating": 9.0,
        "runtime_minutes": 152,
    },
    {
        "title": "Pulp Fiction",
        "year": 1994,
        "director": "Quentin Tarantino",
        "genres": ["Crime", "Drama"],
        "cast": "John Travolta, Uma Thurman, Samuel L. Jackson",
        "description": "The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption.",
        "imdb_rating": 8.9,
        "runtime_minutes": 154,
    },
    {
        "title": "Schindler's List",
        "year": 1993,
        "director": "Steven Spielberg",
        "genres": ["Drama", "Mystery"],
        "cast": "Liam Neeson, Ralph Fiennes, Ben Kingsley",
        "description": "In German-occupied Poland during WWII, industrialist Schindler becomes concerned for his Jewish workforce after witnessing their persecution.",
        "imdb_rating": 9.0,
        "runtime_minutes": 195,
    },
    {
        "title": "Inception",
        "year": 2010,
        "director": "Christopher Nolan",
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "cast": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page",
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea.",
        "imdb_rating": 8.8,
        "runtime_minutes": 148,
    },
    {
        "title": "The Matrix",
        "year": 1999,
        "director": "Lana Wachowski",
        "genres": ["Action", "Sci-Fi"],
        "cast": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        "description": "A computer hacker learns that reality as he knows it is a simulation, and joins a rebellion to fight the controllers.",
        "imdb_rating": 8.7,
        "runtime_minutes": 136,
    },
    {
        "title": "Parasite",
        "year": 2019,
        "director": "Bong Joon Ho",
        "genres": ["Comedy", "Drama", "Thriller"],
        "cast": "Kang-ho Song, Sun-kyun Lee, Yeo-jeong Jo",
        "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "imdb_rating": 8.5,
        "runtime_minutes": 132,
    },
    {
        "title": "Interstellar",
        "year": 2014,
        "director": "Christopher Nolan",
        "genres": ["Adventure", "Drama", "Sci-Fi"],
        "cast": "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
        "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
        "imdb_rating": 8.6,
        "runtime_minutes": 169,
    },
    {
        "title": "The Silence of the Lambs",
        "year": 1991,
        "director": "Jonathan Demme",
        "genres": ["Crime", "Drama", "Thriller"],
        "cast": "Jodie Foster, Anthony Hopkins, Lawrence A. Bonney",
        "description": "A young FBI cadet must receive the help of an incarcerated and manipulative cannibal killer to catch another serial killer.",
        "imdb_rating": 8.6,
        "runtime_minutes": 118,
    },
    {
        "title": "Forrest Gump",
        "year": 1994,
        "director": "Robert Zemeckis",
        "genres": ["Drama", "Romance"],
        "cast": "Tom Hanks, Robin Wright, Gary Sinise",
        "description": "The presidencies of Kennedy and Johnson, events of Vietnam, Watergate and other history unfold through the perspective of an Alabama man.",
        "imdb_rating": 8.8,
        "runtime_minutes": 142,
    },
    {
        "title": "Goodfellas",
        "year": 1990,
        "director": "Martin Scorsese",
        "genres": ["Crime", "Drama"],
        "cast": "Ray Liotta, Robert De Niro, Joe Pesci",
        "description": "The story of Henry Hill and his life in the mob, covering his arrival to his leave, covering 25 years.",
        "imdb_rating": 8.7,
        "runtime_minutes": 146,
    },
    {
        "title": "The Lion King",
        "year": 1994,
        "director": "Roger Allers",
        "genres": ["Animation", "Adventure", "Drama"],
        "cast": "Matthew Broderick, Jeremy Irons, James Earl Jones",
        "description": "Lion prince Simba and his father are targeted by his treacherous uncle, who wants to seize the throne.",
        "imdb_rating": 8.5,
        "runtime_minutes": 88,
    },
    {
        "title": "Spirited Away",
        "year": 2001,
        "director": "Hayao Miyazaki",
        "genres": ["Animation", "Adventure", "Fantasy"],
        "cast": "Daveigh Chase, Suzanne Pleshette, Miyu Irino",
        "description": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches and spirits.",
        "imdb_rating": 8.6,
        "runtime_minutes": 125,
    },
    {
        "title": "Avengers: Endgame",
        "year": 2019,
        "director": "Anthony Russo",
        "genres": ["Action", "Adventure", "Drama"],
        "cast": "Robert Downey Jr., Chris Evans, Mark Ruffalo",
        "description": "After the devastating events of Infinity War, the Avengers assemble once more to reverse Thanos's actions.",
        "imdb_rating": 8.4,
        "runtime_minutes": 181,
    },
    {
        "title": "The Grand Budapest Hotel",
        "year": 2014,
        "director": "Wes Anderson",
        "genres": ["Adventure", "Comedy", "Crime"],
        "cast": "Ralph Fiennes, F. Murray Abraham, Tony Revolori",
        "description": "A writer encounters the owner of an aging European hotel who tells him of his early days serving as a lobby boy.",
        "imdb_rating": 8.1,
        "runtime_minutes": 99,
    },
    {
        "title": "Get Out",
        "year": 2017,
        "director": "Jordan Peele",
        "genres": ["Horror", "Mystery", "Thriller"],
        "cast": "Daniel Kaluuya, Allison Williams, Bradley Whitford",
        "description": "A young African-American visits his white girlfriend's parents for the weekend, where his simmering uneasiness about their reception grows.",
        "imdb_rating": 7.7,
        "runtime_minutes": 104,
    },
    {
        "title": "Everything Everywhere All at Once",
        "year": 2022,
        "director": "Daniel Kwan",
        "genres": ["Action", "Adventure", "Comedy"],
        "cast": "Michelle Yeoh, Stephanie Hsu, Ke Huy Quan",
        "description": "An aging Chinese immigrant is swept up in an insane adventure, where she alone can save the world by exploring other universes.",
        "imdb_rating": 7.8,
        "runtime_minutes": 139,
    },
    {
        "title": "Oppenheimer",
        "year": 2023,
        "director": "Christopher Nolan",
        "genres": ["Drama", "Mystery"],
        "cast": "Cillian Murphy, Emily Blunt, Matt Damon",
        "description": "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during WWII.",
        "imdb_rating": 8.3,
        "runtime_minutes": 180,
    },
    {
        "title": "Barbie",
        "year": 2023,
        "director": "Greta Gerwig",
        "genres": ["Adventure", "Comedy", "Fantasy"],
        "cast": "Margot Robbie, Ryan Gosling, America Ferrera",
        "description": "Barbie suffers a crisis that leads her to question her world and herself. She sets off on a journey of self-discovery.",
        "imdb_rating": 6.8,
        "runtime_minutes": 114,
    },
    {
        "title": "No Country for Old Men",
        "year": 2007,
        "director": "Joel Coen",
        "genres": ["Crime", "Drama", "Thriller"],
        "cast": "Tommy Lee Jones, Javier Bardem, Josh Brolin",
        "description": "Violence and mayhem ensue after a hunter stumbles upon a drug deal gone wrong and picks up a bag with $2 million.",
        "imdb_rating": 8.2,
        "runtime_minutes": 122,
    },
    {
        "title": "Mad Max: Fury Road",
        "year": 2015,
        "director": "George Miller",
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "cast": "Tom Hardy, Charlize Theron, Nicholas Hoult",
        "description": "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland.",
        "imdb_rating": 8.1,
        "runtime_minutes": 120,
    },
    {
        "title": "Hereditary",
        "year": 2018,
        "director": "Ari Aster",
        "genres": ["Drama", "Horror", "Mystery"],
        "cast": "Toni Collette, Gabriel Byrne, Alex Wolff",
        "description": "A grieving family is haunted by tragic and disturbing occurrences after the death of their secretive grandmother.",
        "imdb_rating": 7.3,
        "runtime_minutes": 127,
    },
    {
        "title": "The Truman Show",
        "year": 1998,
        "director": "Peter Weir",
        "genres": ["Comedy", "Drama"],
        "cast": "Jim Carrey, Laura Linney, Noah Emmerich",
        "description": "An insurance salesman discovers his whole life is actually a reality TV show.",
        "imdb_rating": 8.2,
        "runtime_minutes": 103,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample movies and genres'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating genres...')
        genres = {}
        for name in GENRES_DATA:
            g, _ = Genre.objects.get_or_create(name=name)
            genres[name] = g

        self.stdout.write('Creating movies...')
        created_count = 0
        for data in MOVIES_DATA:
            movie, created = Movie.objects.get_or_create(
                title=data['title'],
                year=data['year'],
                defaults={
                    'director': data.get('director', ''),
                    'cast': data.get('cast', ''),
                    'description': data.get('description', ''),
                    'imdb_rating': data.get('imdb_rating', 0.0),
                    'runtime_minutes': data.get('runtime_minutes', 0),
                    'poster_url': '',
                }
            )
            if created:
                for genre_name in data.get('genres', []):
                    if genre_name in genres:
                        movie.genres.add(genres[genre_name])
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Done! Created {created_count} movies and {len(genres)} genres.'
        ))
