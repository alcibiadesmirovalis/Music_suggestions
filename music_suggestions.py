import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

# Spotify API Credentials (Replace these with your actual credentials)
CLIENT_ID = "d05c6779b6ef4f1e92b2c4825dc1f797"
CLIENT_SECRET = "8d7b090e6a7f4edea69be540fb425ac9"

DEFAULT_GENRES = [
    "pop", "rock", "hip-hop", "electronic", "indie",
    "jazz", "metal", "classical", "dance", "ambient", "r&b", "blues", "soul", "punk", "reggae"
]

# Update genre mappings with subgenres
GENRE_MAPPINGS = {
    'electronic': {
        'seeds': ['electronic', 'edm', 'house', 'techno', 'trance', 'electro'],
        'target_attributes': {
            'target_energy': 0.8,
            'target_danceability': 0.7,
            'min_popularity': 45,
            'min_instrumentalness': 0.4,
            'target_tempo': 128,
            'min_tempo': 120,
            'max_acousticness': 0.4
        }
    },
    'rock': {
        'seeds': ['rock', 'alternative', 'metal'],
        'target_attributes': {
            'target_energy': 0.7,
            'min_popularity': 50,
            'target_instrumentalness': 0.3
        }
    }
    # Add more genre mappings as needed
}

def initialize_spotify():
    """Initialize and authenticate the Spotify client with proper error handling."""
    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # Test authentication
        sp.search(q="test", type="track", limit=1)
        
        return sp
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

def get_detailed_track_info(sp, track_ids):
    """Get detailed information for multiple tracks using Spotify's tracks endpoint"""
    try:
        # Ensure track_ids is a list and remove any None values
        track_ids = [tid for tid in track_ids if tid]
        if not track_ids:
            return []
            
        # Split track IDs into chunks of 50 (API limit)
        chunks = [track_ids[i:i + 50] for i in range(0, len(track_ids), 50)]
        detailed_tracks = []
        
        for chunk in chunks:
            # Format IDs as comma-separated string
            ids_string = ','.join(chunk)
            results = sp.tracks(
                tracks=chunk,
                market='US'
            )
            
            if results and 'tracks' in results:
                # Filter out None values and add valid tracks
                valid_tracks = [t for t in results['tracks'] if t is not None]
                detailed_tracks.extend(valid_tracks)
        
        return detailed_tracks
        
    except Exception as e:
        print(f"Error getting track details: {e}")
        return []

def format_track_info(track):
    """Format track information with additional details"""
    try:
        # Basic track info
        artists = ', '.join(artist['name'] for artist in track['artists'])
        name = track['name']
        album = track['album']['name']
        
        # Duration formatting
        duration_min = track['duration_ms'] // 1000 // 60
        duration_sec = (track['duration_ms'] // 1000) % 60
        
        # Additional metadata
        popularity = track['popularity']
        preview_url = 'Available' if track.get('preview_url') else 'Not Available'
        external_url = track['external_urls'].get('spotify', 'Not Available')
        
        return (
            f"{name} - {artists}\n"
            f"   Album: {album}\n"
            f"   Duration: {duration_min}:{duration_sec:02d}\n"
            f"   Popularity: {popularity}/100\n"
            f"   Preview: {preview_url}\n"
            f"   Spotify URL: {external_url}"
        )
    except Exception as e:
        print(f"Error formatting track: {e}")
        return f"{track.get('name', 'Unknown')} - {track['artists'][0]['name'] if track.get('artists') else 'Unknown'}"

def search_spotify(sp, query, search_type='track', advanced_search=None):
    """Enhanced search function using Spotify's Search API with advanced parameters"""
    try:
        # Build search query with filters
        if advanced_search:
            filters = []
            if 'year' in advanced_search:
                filters.append(f"year:{advanced_search['year']}")
            if 'genre' in advanced_search:
                filters.append(f"genre:{advanced_search['genre']}")
            if 'artist' in advanced_search:
                filters.append(f"artist:{advanced_search['artist']}")
            
            query = f"{query} {' '.join(filters)}"

        # Perform search with parameters
        results = sp.search(
            q=query,
            type=search_type,
            market='US',
            limit=50,  # Get more results for better filtering
            offset=0
        )
        
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return None

def get_available_genres(sp):
    """Get all available genres from Spotify"""
    try:
        genres = sp.recommendation_genre_seeds()
        return genres['genres']
    except Exception as e:
        print(f"Error getting genres: {e}")
        return DEFAULT_GENRES

def get_genre_recommendations(sp, genre):
    """Get recommendations for a specific genre using multiple seed genres"""
    try:
        genre_info = GENRE_MAPPINGS.get(genre.lower(), {
            'seeds': [genre],
            'target_attributes': {'min_popularity': 50}
        })
        
        # Store all found tracks to avoid duplicates
        all_tracks = set()
        result_tracks = []
        
        # Try multiple combinations of seeds
        seeds = genre_info['seeds']
        random.shuffle(seeds)  # Randomize seed order
        
        for seed in seeds:
            if len(result_tracks) >= 5:
                break
                
            try:
                params = {
                    'seed_genres': [seed],
                    'limit': 20,
                    'market': 'US',
                    **genre_info['target_attributes']
                }
                
                recommendations = sp.recommendations(**params)
                if recommendations and recommendations.get('tracks'):
                    for track in recommendations['tracks']:
                        track_key = f"{track['name']}:{track['artists'][0]['name']}"
                        if track_key not in all_tracks:
                            all_tracks.add(track_key)
                            # Verify genre match using artist's genres
                            try:
                                artist_info = sp.artist(track['artists'][0]['id'])
                                artist_genres = [g.lower() for g in artist_info['genres']]
                                if any(s in ' '.join(artist_genres) for s in genre_info['seeds']):
                                    result_tracks.append(track)
                            except:
                                continue
            except:
                continue
            
        # If we still don't have enough tracks, try search
        if len(result_tracks) < 5:
            search_results = sp.search(
                q=f"genre:{genre}",
                type='track',
                market='US',
                limit=50
            )
            if search_results and search_results['tracks']['items']:
                for track in search_results['tracks']['items']:
                    track_key = f"{track['name']}:{track['artists'][0]['name']}"
                    if track_key not in all_tracks and len(result_tracks) < 5:
                        all_tracks.add(track_key)
                        result_tracks.append(track)
        
        # Sort by popularity and return top 5
        result_tracks.sort(key=lambda x: x['popularity'], reverse=True)
        return result_tracks[:5]
        
    except Exception as e:
        print(f"Error getting genre recommendations: {e}")
        return []

def get_genre_tracks(sp, genre):
    """Get tracks for a genre using enhanced search"""
    try:
        if genre not in DEFAULT_GENRES:
            return [f"Invalid genre: {genre}. Try one of these: {', '.join(DEFAULT_GENRES)}"]
        
        # Try different search approaches
        search_results = search_spotify(sp, 
            genre,
            search_type='track',
            advanced_search={'genre': genre, 'year': '2020-2024'}
        )
        
        if not search_results or not search_results.get('tracks', {}).get('items'):
            return [f"No tracks found for genre: {genre}"]

        tracks = search_results['tracks']['items']
        
        # Enhanced filtering
        filtered_tracks = []
        for track in tracks:
            try:
                # Get artist genres
                artist_id = track['artists'][0]['id']
                artist_info = sp.artist(artist_id)
                artist_genres = [g.lower() for g in artist_info['genres']]
                
                # Check if track matches genre
                if (any(genre.lower() in g for g in artist_genres) and 
                    track['popularity'] > 30):
                    filtered_tracks.append(track)
            except:
                continue
        
        # Sort by popularity
        filtered_tracks.sort(key=lambda x: x['popularity'], reverse=True)
        
        return [format_track_info(track) for track in filtered_tracks[:5]]

    except Exception as e:
        print(f"Error: {e}")
        return ["Error fetching genre tracks. Please try again."]

def get_artist_recommendations(sp, artist_name):
    """Get recommendations based on artist with enhanced search"""
    try:
        # Search for the artist with additional parameters
        search_results = search_spotify(sp,
            artist_name,
            search_type='artist,track',
            advanced_search={'artist': artist_name}
        )
        
        if not search_results or not search_results.get('artists', {}).get('items'):
            return [f"No artist found with name: {artist_name}"]
        
        artist = search_results['artists']['items'][0]
        artist_id = artist['id']
        
        # Collect tracks from multiple sources
        tracks_pool = []
        
        # 1. Get artist's top tracks
        top_tracks = sp.artist_top_tracks(artist_id, country="US")['tracks']
        tracks_pool.extend([(track, 'Top Track') for track in top_tracks[:3]])
        
        # 2. Get similar artists' tracks
        similar_artists = sp.artist_related_artists(artist_id)['artists'][:3]
        for similar in similar_artists:
            similar_top = sp.artist_top_tracks(similar['id'], country="US")['tracks']
            tracks_pool.extend([(track, f"Similar to {similar['name']}") 
                              for track in similar_top[:2]])
        
        # Format and return results
        formatted_tracks = []
        for track, source in tracks_pool[:5]:
            track_info = format_track_info(track)
            formatted_tracks.append(f"{track_info}\n   Source: {source}")
        
        return formatted_tracks

    except Exception as e:
        print(f"Error: {e}")
        return ["Error fetching artist tracks. Please try again."]

def get_recommendations(genre=None, artist=None):
    """Get music recommendations based on genre or artist"""
    sp = initialize_spotify()
    if not sp:
        return ["Could not connect to Spotify. Please check your credentials."]
    
    try:
        if genre:
            genre = genre.lower().strip()
            tracks = get_genre_recommendations(sp, genre)
            if not tracks:
                return [f"No tracks found for genre: {genre}"]
            return [format_track_info(track) for track in tracks]
        elif artist:
            return get_artist_recommendations(sp, artist.strip())
        else:
            random_genre = random.choice(DEFAULT_GENRES)
            return get_genre_tracks(sp, random_genre)
            
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return ["Error getting recommendations. Please try again."]

if __name__ == "__main__":
    print("Welcome to the Spotify Music Suggestor!")
    sp = initialize_spotify()
    if sp:
        print("\nAvailable genres:", ", ".join(sorted(get_available_genres(sp))))
    
    print("\nHow to use:")
    print("1. For genre recommendations, type 'genre:' followed by a genre")
    print("2. For artist recommendations, type 'artist:' followed by a name")
    print("3. Or just press Enter for random suggestions\n")
    
    while True:
        user_input = input("Enter 'genre:GENRE' or 'artist:ARTIST' (or 'exit' to quit): ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
        
        if user_input.lower().startswith("genre:"):
            genre = user_input.split(":", 1)[1].strip()
            suggestions = get_recommendations(genre=genre)
        elif user_input.lower().startswith("artist:"):
            artist = user_input.split(":", 1)[1].strip()
            suggestions = get_recommendations(artist=artist)
        else:
            suggestions = get_recommendations()
        
        print("\nHere are your suggestions:")
        for i, song in enumerate(suggestions, 1):
            print(f"{i}. {song}")
        print()
