import json
import os
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

class MemoryManager:
    """Manages the long-term user profile memory using a JSON file."""

    def __init__(self, profile_path="user_profile.json"):
        """
        Initializes the MemoryManager.

        Args:
            profile_path (str): The path to the JSON file storing the user profile.
        """
        self.profile_path = profile_path
        self.profile = {}
        self.load_profile()

    def load_profile(self):
        """Loads the user profile from the JSON file."""
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    self.profile = json.load(f)
                print(f"{Fore.CYAN}Loaded user profile from {self.profile_path}{Fore.RESET}")
            except json.JSONDecodeError:
                print(f"{Fore.RED}Error decoding JSON from {self.profile_path}. Starting with an empty profile.{Fore.RESET}")
                self.profile = {}
            except Exception as e:
                print(f"{Fore.RED}Error loading profile from {self.profile_path}: {e}{Fore.RESET}")
                self.profile = {}
        else:
            print(f"{Fore.YELLOW}Profile file {self.profile_path} not found. Starting with an empty profile.{Fore.RESET}")
            self.profile = {}

    def save_profile(self):
        """Saves the current user profile to the JSON file."""
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(self.profile, f, indent=4)
            # print(f"{Fore.CYAN}User profile saved to {self.profile_path}{Fore.RESET}") # Optional: Can be noisy
        except Exception as e:
            print(f"{Fore.RED}Error saving profile to {self.profile_path}: {e}{Fore.RESET}")

    def update_profile(self, key, value):
        """
        Updates a specific key in the user profile.
        For simplicity, this currently overwrites the key.
        Future enhancements could handle appending to lists, etc.

        Args:
            key (str): The key in the profile to update (e.g., 'liked_genres').
            value (any): The value to set for the key.
        """
        self.profile[key] = value
        # print(f"{Fore.MAGENTA}Profile updated: {{'{key}': {value}}}{Fore.RESET}") # Optional: For debugging

    def get_profile(self):
        """Returns the entire user profile dictionary."""
        return self.profile

    def get_profile_summary(self):
        """Generates a simple string summary of the user profile."""
        if not self.profile:
            return "No profile information available yet."

        summary_lines = []
        for key, value in self.profile.items():
            summary_lines.append(f"- {key.replace('_', ' ').capitalize()}: {value}")
        return "\n".join(summary_lines)

    def clear_profile(self):
        """Clears the profile in memory and deletes the profile file."""
        self.profile = {}
        if os.path.exists(self.profile_path):
            try:
                os.remove(self.profile_path)
                print(f"{Fore.YELLOW}Cleared profile and deleted {self.profile_path}{Fore.RESET}")
            except Exception as e:
                print(f"{Fore.RED}Error deleting profile file {self.profile_path}: {e}{Fore.RESET}")
        else:
             print(f"{Fore.YELLOW}Cleared profile in memory (file did not exist).{Fore.RESET}")
