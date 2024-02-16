from django.core.management import BaseCommand

from jcourse_api.utils import rename_user_by_name, rename_user_raw_account


class Command(BaseCommand):
    help = 'Rename users'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--old', type=str)
        parser.add_argument('-n', '--new', type=str)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--hash', action="store_true", help='rename by hashed username')
        group.add_argument('--raw', action="store_true", help='rename by raw account')

    def handle(self, *args, **options):
        if options['old'] and options['new']:
            if options['hash']:
                rename_user_by_name(options['old'], options['new'])
            elif options['raw']:
                rename_user_raw_account(options['old'], options['new'])
        else:
            self.stdout.write(f'No value provided!')
        self.stdout.write('Result: renamed')
