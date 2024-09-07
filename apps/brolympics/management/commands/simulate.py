from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from brolympics.models import *
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Simulates a Brolympics'

    def handle(self, *args, **options):
        player_list = [
            'Jacob Simerly',
            'Javi Canales',
            'Tanner Stis',
            'Max Zimmerman',
            'Alex Piroozi',
            'Timmy Becker',
            'Jonathan Gianakos',
            'Bryce Harter',
            'Alex Walker',
            'Davis Hagen',
            'Salvador Matus',
            'Anthony Golden',
            'Brady Johnson',
            'Jake Conrad',
            'Marcus Thompson',
            'Marcus Cousin',
            'Julian Simmerman',
            'David Tsetse',
            'Tanner Dye',
            'Cory Collins'
        ]

        print(len(player_list))