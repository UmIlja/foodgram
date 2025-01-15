import csv
from api.models import Ingredient
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import ingredients from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        # Открываем CSV файл и читаем его
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 2:  # Проверяем, что в строке достаточно данных
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error importing ingredient: '
                            f'row does not contain enough data: {row}'
                        )
                    )
                    continue
                try:
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=row[0].strip(),  # Убираем лишние пробелы
                        defaults={'measurement_unit': row[1].strip()}
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Ingredient "{ingredient.name}" '
                                f'imported successfully!'
                            )
                        )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Ingredient "{ingredient.name}" already exists.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error importing ingredient "{row[0]}": {str(e)}'))
        self.stdout.write(self.style.SUCCESS(
            'All ingredients imported successfully!'))
