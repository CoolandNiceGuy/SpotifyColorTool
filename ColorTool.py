import os
import sys
import json
import spotipy
import spotipy.util as util
import cv2
import numpy as np
from json.decoder import JSONDecodeError
from sklearn.cluster import KMeans
from collections import Counter
from PIL import Image
import requests
from io import BytesIO

def getDominantColor(image):
    """
    takes image as an input
    converts image to HSV format
    returns dominant color of image
    dominant color is found by running k-means on the pixels and
    returning the centroid of the largest cluster
    """

    #convert image to array of pixels
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    #change k to get different results
    k = 2

    clt = KMeans(n_clusters = k)
    labels = clt.fit_predict(image)

    #count labels to find most popular
    label_counts = Counter(labels)

    #Get most popular centroid
    dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]

    return list(dominant_color)


def url_to_image(url):
    #download image, conver to numpy array, then read into OpenCV format
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert('RGB')
    open_cv2_img = np.array(img)
    open_cv2_img = cv2.cvtColor(open_cv2_img, cv2.COLOR_RGB2BGR)
    return open_cv2_img


#Get username from terminal
username = sys.argv[1]


# User ID:landonborges

token = util.prompt_for_user_token(username, scope="playlist-modify-public")

# Create Spotify Object
spotifyObject = spotipy.Spotify(auth=token)

user = spotifyObject.current_user()


print("Welcome to Landon's Spotify Color Assistant")

featuredPlaylists = spotifyObject.featured_playlists(country="US", limit=20)


playlistNames = featuredPlaylists["playlists"]["items"]

playlistIDS = []

for item in playlistNames:
    playlistIDS.append(item["id"])

choice = input("What color-inspired playlist would you like to make today? ").lower()
color_min = -1
color_max = -1

if choice == "red":
    color_min = 346
    color_max = 360
elif choice == "orange":
    color_min = 11
    color_max = 50
elif choice == "yellow":
    color_min = 51
    color_max = 80
elif choice == "green":
    color_min = 100
    color_max = 130
elif choice == "blue":
    color_min = 170
    color_max = 240
elif choice == "purple":
    color_min = 241
    color_max = 320
elif choice == "pink":
    color_min = 321
    color_max = 345
else:
    print("invalid input. Exiting...")
    sys.exit(0)

# Choices = Red, Orange, Yellow, Green, Blue, Purple, Pink

#iterate through playlistIDS, parse each song of each playlist and check art color: O(n^2)

playlist_songs = spotifyObject.playlist_items(playlistIDS[0], fields='items.track.album', additional_types=['track'])['items']

valid_IDS = []
for id in playlistIDS:
    #get songs from current playlist
    songs = spotifyObject.playlist_items(id, fields='items.track', additional_types=['track'])['items']

    #get image url's and store in list
    for song in songs:
        img = url_to_image(song['track']['album']['images'][2]['url'])
        hsv_IMG = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # make sure image is desired color
        color = getDominantColor(hsv_IMG)
        hue =  color[0] * 2
        value = color[2]
        saturation = color[1]
        if value > 51 and saturation > 76:
            if (hue > color_min and hue < color_max) or (choice == "red" and (hue > 0 and hue < 10)):
                # print("Adding song \"" + song['track']['name'] + "\" to playlist")
                valid_IDS.append(song['track']['id'])


#now that matching tracks have been found, create playlist and add tracks to themed playlist

spotifyObject.user_playlist_create('landonborges', name=choice, public=True, description="Playlist insipred by color created by Landon's Spotify Tool")

new_playlist = spotifyObject.current_user_playlists(1)

new_playlist_ID = new_playlist["items"][0]["id"]

if len(valid_IDS) < 100:
    spotifyObject.user_playlist_add_tracks('landonborges', new_playlist_ID, valid_IDS[0:len(valid_IDS) - 1])    

spotifyObject.user_playlist_add_tracks('landonborges', new_playlist_ID, valid_IDS[0:100])



print("script is done running") 