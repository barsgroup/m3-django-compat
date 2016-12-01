# coding: utf-8
import json

from m3_django_compat import BaseCommand


class Command(BaseCommand):

    u"""Management-команда для проверки ``m3_django_compat.BaseCommand``."""

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument(
            '--test1', action='store', dest='test1', help='Test 1',
        )
        parser.add_argument(
            '--test2', action='store_true', dest='test2',
            default=False, help='Test 2',
        )
        parser.add_argument(
            '--test3', action='store', dest='test3',
            default=1, type=int, choices=[0, 1, 2, 3],
            help='Test 3',
        )

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(args) + '\n')
        self.stdout.write(json.dumps(options) + '\n')
