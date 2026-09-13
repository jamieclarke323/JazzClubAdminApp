from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('household', '0005_shoppingitem_checked_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportantInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='important_info', to='household.household')),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
