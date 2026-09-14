from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0007_ideaentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='kind',
            field=models.CharField(default='task', max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('household', 'kind', 'name')},
        ),
    ]
