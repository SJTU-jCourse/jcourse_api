from django.core.management import BaseCommand

from jcourse_api.utils import merge_user_by_raw_account, merge_user_by_id


class Command(BaseCommand):
    help = 'Merge users'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--old', type=str)
        parser.add_argument('-n', '--new', type=str)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--uid', action="store_true", help='merge by user id')
        group.add_argument('--raw', action="store_true", help='merge by raw account')

    def handle(self, *args, **options):
        if options['old'] and options['new']:
            if options['uid']:
                merge_user_by_id(options['old'], options['new'])
            elif options['raw']:
                merge_user_by_raw_account(options['old'], options['new'])
        else:
            self.stdout.write(f'No value provided!')
        self.stdout.write('Result: Replaced')
