from django.core.management.base import BaseCommand
from voters.models import Voter


class Command(BaseCommand):
    help = 'Update search_text field for all existing voter records'

    def handle(self, *args, **options):
        self.stdout.write('Updating search_text for all voters...')
        
        voters = Voter.objects.all()
        total = voters.count()
        updated = 0
        
        for i, voter in enumerate(voters.iterator(), 1):
            voter.search_text = voter.build_search_text()
            voter.save(update_fields=['search_text'])
            updated += 1
            
            if i % 500 == 0:
                self.stdout.write(f'  Processed {i}/{total} voters...')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} voters'))
