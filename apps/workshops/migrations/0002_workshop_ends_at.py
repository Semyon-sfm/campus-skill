from datetime import datetime, timedelta

from django.db import migrations, models
from django.utils import timezone


def fill_ends_at(apps, schema_editor):
    Workshop = apps.get_model("workshops", "Workshop")
    tz = timezone.get_current_timezone()
    for workshop in Workshop.objects.all():
        starts_at = timezone.make_aware(datetime.combine(workshop.date, workshop.time), tz)
        workshop.ends_at = starts_at + timedelta(minutes=workshop.duration)
        workshop.save(update_fields=["ends_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("workshops", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workshop",
            name="ends_at",
            field=models.DateTimeField(
                db_index=True, editable=False, null=True, verbose_name="окончание"
            ),
        ),
        migrations.RunPython(fill_ends_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="workshop",
            name="ends_at",
            field=models.DateTimeField(db_index=True, editable=False, verbose_name="окончание"),
        ),
    ]
