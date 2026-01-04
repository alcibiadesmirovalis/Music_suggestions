import requests
import base64

CLIENT_ID = "d05c6779b6ef4f1e92b2c4825dc1f797"
CLIENT_SECRET = "8d7b090e6a7f4edea69be540fb425ac9"

def get_access_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return None

def search_artist_by_name(artist_name, token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'q': f'artist:"{artist_name}"',
        'type': 'artist',
        'limit': 10
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['artists']['items']
    else:
        return None

def get_artist_top_tracks(artist_id, token):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'market': 'US'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['tracks']
    else:
        return None

def get_search_suggestions(partial_name, token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'q': partial_name,
        'type': 'artist',
        'limit': 10
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['artists']['items']
    return None

def get_track_suggestions(partial_name, token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'q': partial_name,
        'type': 'track',
        'limit': 5
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['tracks']['items']
    return None

def display_track_info(track):
    artists = ", ".join([artist['name'] for artist in track['artists']])
    print(f"Track: {track['name']}")
    print(f"Artists: {artists}")
    print(f"Album: {track['album']['name']}")
    print("-" * 40)

if __name__ == "__main__":
    print("Start typing to search (press Enter to see suggestions, type 'done' to select):")
    token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    
    if not token:
        print("Failed to retrieve access token")
        exit()

    search_term = ""
    while True:
        search_term = input("> ")
        if search_term.lower() == 'done':
            break
        if len(search_term) >= 2:
            print("\nArtist Suggestions:")
            artist_suggestions = get_search_suggestions(search_term, token)
            if artist_suggestions:
                for i, artist in enumerate(artist_suggestions, 1):
                    print(f"A{i}. {artist['name']}")
            else:
                print("No artist suggestions found")

            print("\nTrack Suggestions:")
            track_suggestions = get_track_suggestions(search_term, token)
            if track_suggestions:
                for i, track in enumerate(track_suggestions, 1):
                    artists = ", ".join([artist['name'] for artist in track['artists']])
                    print(f"T{i}. {track['name']} - by {artists}")
            else:
                print("No track suggestions found")

            print("\nTo select, type 'A1'-'A5' for artists or 'T1'-'T5' for tracks, or keep typing to search:")

            choice = input("Selection (or press Enter to continue): ").strip().upper()
            if choice.startswith('A') and artist_suggestions:
                try:
                    idx = int(choice[1:]) - 1
                    if 0 <= idx < len(artist_suggestions):
                        artist = artist_suggestions[idx]
                        print(f"\nSelected Artist: {artist['name']}")
                        tracks = get_artist_top_tracks(artist['id'], token)
                        if tracks:
                            print("Top Tracks:")
                            for track in tracks:
                                print(f"  - {track['name']}")
                        break
                except ValueError:
                    pass
            elif choice.startswith('T') and track_suggestions:
                try:
                    idx = int(choice[1:]) - 1
                    if 0 <= idx < len(track_suggestions):
                        print("\nSelected Track Details:")
                        display_track_info(track_suggestions[idx])
                        break
                except ValueError:
                    pass

    # Remove or comment out the old search code below
    # if search_term and search_term.lower() != 'done':
    #     ...existing code...
