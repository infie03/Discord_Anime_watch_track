import json
import os
import random
from datetime import datetime

class Anime:
    def __init__(self, title, status, preference, genre='Unknown', episodes_watched=0, total_episodes=1, start_date=None, completed_date=None, source_link=None, favorite=False):
        self.title = title
        self.status = status  # 'Completed', 'To Watch', 'Watching'
        self.preference = preference  # 'High', 'Medium', 'Low'
        self.genre = genre
        self.episodes_watched = episodes_watched
        self.total_episodes = total_episodes
        self.start_date = start_date
        self.completed_date = completed_date
        self.source_link = source_link
        self.favorite = favorite

    def update_progress(self, episodes):
        self.episodes_watched = min(episodes, self.total_episodes)
        if self.episodes_watched == self.total_episodes:
            self.status = 'Completed'
            self.completed_date = datetime.today().strftime('%Y-%m-%d')

    def __repr__(self):
        progress = f"[{self.episodes_watched}/{self.total_episodes}]" if self.status == 'Watching' else ""
        return f"{self.title} ({self.status} - {self.preference} Priority - {self.genre}) {progress}"

class AnimeWatchList:
    def __init__(self, data_file='anime_list.json'):
        self.data_file = data_file
        self.anime_list = []
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file) or '.', exist_ok=True)
        self.load_data()

    def add_anime(self, anime):
        if anime.status == 'Watching' and anime.start_date is None:
            anime.start_date = datetime.today().strftime('%Y-%m-%d')
        self.anime_list.append(anime)
        self.save_data()

    def delete_anime(self, index):
        if 0 <= index < len(self.anime_list) and not self.anime_list[index].favorite:
            del self.anime_list[index]
            self.save_data()

    def update_status(self, index, new_status):
        if 0 <= index < len(self.anime_list):
            anime = self.anime_list[index]
            anime.status = new_status
            if new_status == 'Watching' and anime.start_date is None:
                anime.start_date = datetime.today().strftime('%Y-%m-%d')
            elif new_status == 'Completed':
                anime.completed_date = datetime.today().strftime('%Y-%m-%d')
            self.save_data()

    def update_progress(self, index, episodes):
        if 0 <= index < len(self.anime_list):
            self.anime_list[index].update_progress(episodes)
            self.save_data()

    def mark_favorite(self, index):
        if 0 <= index < len(self.anime_list):
            self.anime_list[index].favorite = not self.anime_list[index].favorite
            self.save_data()

    def search_anime(self, keyword):
        return [anime for anime in self.anime_list if keyword.lower() in anime.title.lower()]

    def show_favorites(self):
        return [anime for anime in self.anime_list if anime.favorite]

    def pick_random_anime(self):
        non_completed = [anime for anime in self.anime_list if anime.status != 'Completed']
        return random.choice(non_completed) if non_completed else None

    def get_anime_details(self, index):
        if 0 <= index < len(self.anime_list):
            anime = self.anime_list[index]
            return vars(anime)
        return None

    def list_anime(self):
        for i, anime in enumerate(self.anime_list):
            print(f"{i}. {anime}")

    def save_data(self):
        data = [{'title': a.title, 'status': a.status, 'preference': a.preference, 
                 'genre': a.genre, 'episodes_watched': a.episodes_watched, 
                 'total_episodes': a.total_episodes, 'start_date': a.start_date, 
                 'completed_date': a.completed_date, 'source_link': a.source_link, 
                 'favorite': a.favorite} for a in self.anime_list]
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.data_file) or '.', exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.anime_list = [Anime(**item) for item in data]
    