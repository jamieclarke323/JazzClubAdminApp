from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0008_category_kind'),
    ]

    operations = [
        migrations.AddField(
            model_name='ideaentry',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]
