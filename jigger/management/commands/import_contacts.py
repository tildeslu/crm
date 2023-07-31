from django.core.management.base import BaseCommand, CommandError

import argparse

from jigger.models import Contact, ContactTag

class Command(BaseCommand):
    help = 'Imports contacts to the system adding specified tags'

    def add_arguments(self, parser):
        parser.add_argument('--tag', action='append', nargs=1, default=[])
        parser.add_argument('file', type=argparse.FileType('r'))

    def handle(self, *args, **options):
        tags = []
        for tag_name in options['tag']:
            tag_name = tag_name[0]
            try:
                tag = ContactTag.objects.get(name__exact=tag_name)
            except ContactTag.DoesNotExist:
                raise CommandError('Tag "%s" does not exist' % tag_name)

            tags.append(tag)

        contacts_file = options['file']
        for line in contacts_file:
            msisdn = line.strip().replace("+","")
            self.stdout.write("Processing contact [{}]".format(msisdn))
            contact = Contact.objects.filter(msisdn__exact=msisdn).first()
            if not contact:
                contact = Contact(msisdn=msisdn, name=f"Auto-import +{msisdn}")
                contact.save()
            contact.tags.add(*tags)

        #self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
