from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0006_importantinfo'),
    ]

    operations = [
        migrations.DeleteModel(name='ImportantInfo'),
        migrations.CreateModel(
            name='IdeaEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[
                    ('important_info', 'Important info'),
                    ('recipe', 'Recipe idea'),
                    ('date', 'Date idea'),
                    ('restaurant', 'Restaurant recommendation'),
                    ('film_tv', 'Film/TV recommendation'),
                ], max_length=20)),
                ('title', models.CharField(max_length=45)),
                ('detail', models.TextField(blank=True, max_length=5000)),
                ('effort', models.CharField(blank=True, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], max_length=20)),
                ('recommended_by', models.CharField(blank=True, max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='idea_entries', to='household.category')),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='idea_entries', to='household.household')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name_plural': 'idea entries',
            },
        ),
    ]
