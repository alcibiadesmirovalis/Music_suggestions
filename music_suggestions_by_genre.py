import requests
import base64
import random
from typing import List, Optional, Dict

CLIENT_ID = "d05c6779b6ef4f1e92b2c4825dc1f797"
CLIENT_SECRET = "8d7b090e6a7f4edea69be540fb425ac9"

GENRE_MAPPINGS = {
    'afro': {
        'target_attributes': {
            'target_energy': 0.8,
            'target_danceability': 0.8,
            'min_popularity': 20,
            'target_tempo': 120,
            'target_valence': 0.7
        }
    },
    'alternative': {
        'target_attributes': {
            'target_energy': 0.7,
            'target_danceability': 0.5,
            'min_popularity': 30,
            'target_instrumentalness': 0.3,
            'max_acousticness': 0.6
        }
    },
    'ambient': {
        'target_attributes': {
            'target_energy': 0.3,
            'max_danceability': 0.4,
            'target_instrumentalness': 0.8,
            'min_acousticness': 0.5,
            'max_tempo': 100
        }
    },
    'classical': {
        'target_attributes': {
            'target_energy': 0.3,
            'max_danceability': 0.3,
            'target_instrumentalness': 0.9,
            'min_acousticness': 0.7,
            'max_tempo': 90
        }
    },
    'dance': {
        'target_attributes': {
            'target_energy': 0.8,
            'target_danceability': 0.8,
            'max_instrumentalness': 0.3,
            'target_tempo': 128,
            'min_tempo': 120
        }
    },
    'electronic': {
        'target_attributes': {
            'target_energy': 0.8,
            'target_danceability': 0.7,
            'min_instrumentalness': 0.4,
            'target_tempo': 128,
            'min_tempo': 120,
            'max_acousticness': 0.4
        }
    },
    'jazz': {
        'target_attributes': {
            'target_energy': 0.5,
            'target_instrumentalness': 0.7,
            'min_acousticness': 0.6,
            'max_loudness': -8
        }
    },
    'metal': {
        'target_attributes': {
            'min_energy': 0.8,
            'target_energy': 0.9,
            'max_acousticness': 0.3,
            'target_tempo': 140,
            'min_valence': 0.3
        }
    },
    'pop': {
        'target_attributes': {
            'target_energy': 0.7,
            'target_danceability': 0.7,
            'max_instrumentalness': 0.2,
            'target_valence': 0.6
        }
    },
    'rock': {
        'target_attributes': {
            'target_energy': 0.8,
            'min_popularity': 30,
            'max_instrumentalness': 0.3,
            'min_tempo': 110
        }
    }
}

def get_access_token() -> Optional[str]:
    """
    Get Spotify access token using client credentials
    """
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        return None

def get_available_genres(access_token: str) -> Optional[List[Dict[str, str]]]:
    """
    Fetch available genres from Spotify API using browse categories
    Returns a list of dictionaries containing category id and name
    """
    all_categories = []
    url = "https://api.spotify.com/v1/browse/categories"
    
    # List of major markets to get more categories
    markets = ["US", "GB", "JP", "DE", "FR", "IT", "ES", "BR", "MX", "AU", "GR"]
    
    for market in markets:
        params = {
            "limit": 50,  # Maximum allowed by API
            "offset": 0,
            "country": market,
            "locale": "en_US"
        }
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            categories = response.json()['categories']['items']
            
            # Add new unique categories and split compound categories
            for cat in categories:
                if "Dance/Electronic" in cat['name']:
                    # Split into two categories with same ID but different names
                    dance_cat = {"id": cat['id'], "name": "Dance"}
                    electronic_cat = {"id": cat['id'], "name": "Electronic"}
                    
                    if not any(existing['name'] == "Dance" for existing in all_categories):
                        all_categories.append(dance_cat)
                    if not any(existing['name'] == "Electronic" for existing in all_categories):
                        all_categories.append(electronic_cat)
                elif not any(existing['id'] == cat['id'] for existing in all_categories):
                    all_categories.append({"id": cat['id'], "name": cat['name']})
                    
        except requests.exceptions.RequestException as e:
            print(f"Warning: Error fetching genres for market {market}: {e}")
            continue  # Continue with next market if one fails
    
    # Sort categories by name for consistent display
    return sorted(all_categories, key=lambda x: x['name']) if all_categories else None

def get_genre_attributes(genre_name: str) -> Dict:
    """Get appropriate attributes for a genre"""
    # Clean up genre name
    genre_name = genre_name.lower().strip()
    
    # Handle split categories with specific attributes
    if genre_name == "dance":
        return {
            'target_energy': 0.8,
            'target_danceability': 0.8,
            'max_instrumentalness': 0.3,
            'target_tempo': 128,
            'min_tempo': 120,
            'min_popularity': 50  # Increased popularity threshold
        }
    elif genre_name == "electronic":
        return {
            'target_energy': 0.7,
            'target_danceability': 0.7,
            'min_instrumentalness': 0.4,
            'target_tempo': 125,
            'max_acousticness': 0.4,
            'min_popularity': 50  # Increased popularity threshold
        }
    
    # Try to match genre name with our mappings
    for key, value in GENRE_MAPPINGS.items():
        if key.lower() in genre_name.lower():
            attributes = value['target_attributes']
            attributes['min_popularity'] = 40  # Increased popularity threshold
            return attributes
    
    # Default attributes if no specific mapping found
    return {
        'target_energy': 0.5,
        'min_popularity': 40,  # Increased popularity threshold
        'target_danceability': 0.5
    }

def search_by_genre(access_token: str, genre_info: Dict[str, str], limit: int = 20) -> Optional[Dict]:
    """
    Get tracks using multiple methods and markets with genre-specific attributes
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Get genre-specific attributes
    target_attributes = get_genre_attributes(genre_info['name'])
    print("\nUsing genre attributes:", target_attributes)

    def try_search_method() -> Optional[Dict]:
        """Inner function to try direct search with recommendations"""
        search_url = "https://api.spotify.com/v1/search"
        all_tracks = []
        
        try:
            # Clean up genre name and create search queries
            genre_name = genre_info['name'].lower().replace('/', ' ').replace('&', ' ')
            search_queries = [
                f"genre:\"{genre_name}\"",
                genre_name,
                f"tag:\"{genre_name}\""
            ]
            
            for query in search_queries:
                market = random.choice(["US", "GB", "JP", "DE", "FR", "IT", "ES", "BR", "MX", "AU", "GR"])
                offset = random.randint(0, 1000)
                print(f"Trying search query: {query} in market: {market} with offset: {offset}")
                
                response = requests.get(
                    search_url,
                    headers=headers,
                    params={
                        "q": query,
                        "type": "track",
                        "limit": limit * 2,
                        "market": market,
                        "offset": offset
                    }
                )
                response.raise_for_status()
                tracks = response.json()['tracks']['items']
                
                # Filter tracks based on target attributes
                for track in tracks:
                    if track.get('popularity', 100) >= target_attributes.get('min_popularity', 50):
                        all_tracks.append(track)
                
                if len(all_tracks) >= limit:
                    break
            
            if all_tracks:
                selected_tracks = random.sample(all_tracks, min(len(all_tracks), limit))
                print(f"Found {len(selected_tracks)} tracks using search")
                return {"tracks": {"items": selected_tracks}}
            return None
            
        except Exception as e:
            print(f"Search method failed: {str(e)}")
            return None

    def try_playlist_method() -> Optional[Dict]:
        """Inner function to try playlist method using recommendations"""
        try:
            recommendations_url = "https://api.spotify.com/v1/recommendations"
            genre_seed = genre_info['name'].lower().replace('/', ' ').split()[0]  # Use first word of genre
            
            params = {
                "seed_genres": genre_seed,
                "limit": limit * 2,
                **target_attributes
            }
            
            print(f"Trying recommendations with seed genre: {genre_seed}")
            response = requests.get(recommendations_url, headers=headers, params=params)
            
            if response.status_code == 404:
                print("Genre not found in recommendations, trying search method...")
                return None
                
            response.raise_for_status()
            tracks = response.json().get('tracks', [])
            
            if tracks:
                selected_tracks = random.sample(tracks, min(len(tracks), limit))
                print(f"Found {len(selected_tracks)} tracks using recommendations")
                return {"tracks": {"items": selected_tracks}}
            return None
            
        except Exception as e:
            print(f"Recommendation method failed: {str(e)}")
            return None

    # Randomly choose which method to try first
    methods = [try_playlist_method, try_search_method]
    random.shuffle(methods)
    print(f"Trying methods in order: {['Recommendations' if m == try_playlist_method else 'Search' for m in methods]}")
    
    for method in methods:
        result = method()
        if result and result.get('tracks', {}).get('items'):
            return result
    
    return None

def display_genres(genres: List[Dict[str, str]]) -> None:
    """
    Display the available genres in a formatted way with count
    """
    if not genres:
        print("No genres available")
        return
        
    print(f"\nAvailable Spotify Categories ({len(genres)} total):")
    print("-" * 35)
    # Display in columns if there are many categories
    col_width = max(len(genre['name']) for genre in genres) + 10
    for i, genre in enumerate(genres, 1):
        print(f"{i:3d}. {genre['name']:<{col_width}}", end='\n' if i % 2 == 0 else '')
    if len(genres) % 2 != 0:
        print()  # New line if odd number of genres

def display_tracks(tracks_data: Dict) -> None:
    """
    Display track search results
    """
    if not tracks_data or 'tracks' not in tracks_data:
        print("No tracks found")
        return
    
    tracks = tracks_data['tracks']['items']
    if not tracks:
        print("No tracks found for this genre")
        return
        
    print("\nFound Tracks:")
    print("-" * 50)
    for i, track in enumerate(tracks, 1):
        artists = ", ".join(artist['name'] for artist in track['artists'])
        print(f"{i}. {track['name']} - {artists}")
        print(f"   Album: {track['album']['name']}")
        print()

def main():
    while True:
        # Get fresh token for each session
        access_token = get_access_token()
        if not access_token:
            print("Failed to get access token")
            break
        
        # Get fresh genres list
        genres = get_available_genres(access_token)
        if not genres:
            print("Failed to get genres")
            break
        
        while True:
            print("\n" + "="*50)  # Visual separator
            display_genres(genres)
            print("\nEnter 'q' to quit or...")
            print("Enter 'r' to refresh token and genres...")
            choice = input("Enter the number of the category you want to search (1-{}): ".format(len(genres)))
            
            if choice.lower() == 'q':
                print("\nThanks for using the music suggester!")
                return
            
            if choice.lower() == 'r':
                print("\nRefreshing token and genres...")
                break  # Break inner loop to refresh token
                
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(genres):
                    sorted_genres = sorted(genres, key=lambda x: x['name'])
                    selected_genre = sorted_genres[choice_num-1]
                    print(f"\nSearching for tracks in category: {selected_genre['name']}")
                    results = search_by_genre(access_token, selected_genre)
                    if results:
                        display_tracks(results)
                    
                    input("\nPress Enter to continue...")
                else:
                    print("\nInvalid selection. Please try again.")
            except ValueError:
                print("\nPlease enter a valid number, 'q' to quit, or 'r' to refresh.")

if __name__ == "__main__":
    main()
