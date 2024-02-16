from django.core.management import BaseCommand

from jcourse_api.utils import merge_teacher_by_id, merge_course_by_id, replace_course_code_multi


class Command(BaseCommand):
    help = 'Merge courses'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--old', type=str)
        parser.add_argument('-n', '--new', type=str)
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--code', action="store_true", help='merge by code')
        group.add_argument('--cid', action="store_true", help='merge by course id')
        group.add_argument('--tid', action="store_true", help='merge by teacher id')

    def print_merge(self, old, new):
        self.stdout.write(f'found old {old}, new {new}')

    def print_replace(self, old):
        self.stdout.write(f'replace {old}')

    def handle(self, *args, **options):
        if options['old'] and options['new']:
            if options['code']:
                replace_course_code_multi(options['old'], options['new'], self.print_merge, self.print_replace)
            elif options['cid']:
                merge_course_by_id(options['old'], options['new'], self.print_merge)

            elif options['tid']:
                merge_teacher_by_id(options['old'], options['new'], self.print_merge)
        else:
            self.stdout.write(f'No value provided!')
        self.stdout.write('Result: Replaced')
