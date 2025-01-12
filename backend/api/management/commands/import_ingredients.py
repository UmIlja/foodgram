import pandas as pd
from api.models import Ingredient
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import ingredients from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        df = pd.read_csv(csv_file, header=None)

        for index, row in df.iterrows():
            try:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=row[0].strip(),  # Убираем лишние пробелы
                    defaults={'measurement_unit': row[1].strip()}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Ingred "{ingredient.name}" imported successfully!'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Ingred "{ingredient.name}" already exists.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error importing ingredient "{row[0]}": {str(e)}'))

        self.stdout.write(self.style.SUCCESS(
            'All ingredients imported successfully!'))
