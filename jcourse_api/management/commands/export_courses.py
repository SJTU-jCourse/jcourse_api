from django.core.management import BaseCommand

from jcourse_api.utils import export_courses_to_csv


class Command(BaseCommand):
    help = 'Export courses\' base information'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', type=str, help='output filename')
        parser.add_argument('-e', '--encoding', type=str, help='output encoding')

    def handle(self, *args, **options):
        if not options['output']:
            self.stderr.write('Error: Need to provide output filename')
            return

        with open(options['output'], mode='w', newline='') as f:
            export_courses_to_csv(f)
