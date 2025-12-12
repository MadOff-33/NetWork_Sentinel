# Fichier : src/ui.py
# Encodage : utf-8

from colorama import init, Fore, Style
from tabulate import tabulate
import os

# Initialisation de colorama pour que les couleurs fonctionnent sous Windows
init(autoreset=True)

class ConsoleUI:
    """
    Gère tous les affichages de la console pour une UX cohérente.
    """
    
    @staticmethod
    def clear_screen():
        """Nettoie l'écran du terminal."""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def header(title):
        """Affiche un en-tête stylisé."""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
        print(f"{title.center(60)}")
        print(f"{'='*60}{Style.RESET_ALL}\n")

    @staticmethod
    def log_info(message):
        """Affiche une information neutre."""
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {message}")

    @staticmethod
    def log_success(message):
        """Affiche un succès."""
        print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {message}")

    @staticmethod
    def log_warning(message):
        """Affiche un avertissement."""
        print(f"{Fore.YELLOW}[ATTENTION]{Style.RESET_ALL} {message}")

    @staticmethod
    def log_error(message):
        """Affiche une erreur critique."""
        print(f"{Fore.RED}[ERREUR]{Style.RESET_ALL} {message}")

    @staticmethod
    def display_table(data, headers):
        """
        Affiche un tableau propre à partir d'une liste de données.
        :param data: Liste de listes ou de dictionnaires
        :param headers: Liste des titres de colonnes
        """
        print("\n" + tabulate(data, headers=headers, tablefmt="fancy_grid"))# Fichier : ui.py
# Encodage : utf-8
