import csv
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandParser
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from CSV or JSON file'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--from', 
            dest='source', 
            required=True, 
            help='Path to CSV or JSON file'
        )

    def handle(self, *args, **options):
        source = options['source']
        path = Path(source)
        if not path.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {source}'))
            return
        count = 0
        if path.suffix.lower() == '.csv':
            with path.open(encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    name, measurement_unit = row[0], row[1]
                    Ingredient.objects.get_or_create(name=name, measurement_unit=measurement_unit)
                    count += 1
        elif path.suffix.lower() == '.json':
            with path.open(encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    Ingredient.objects.get_or_create(
                        name=item['name'], 
                        measurement_unit=item['measurement_unit']
                    )
                    count += 1
        else:
            self.stderr.write(
                self.style.ERROR('Unsupported format. Use .csv or .json')
            )
            return
        self.stdout.write(
            self.style.SUCCESS(f'Loaded {count} ingredients')
        )

