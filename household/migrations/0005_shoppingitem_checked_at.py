from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0004_undoentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppingitem',
            name='checked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
