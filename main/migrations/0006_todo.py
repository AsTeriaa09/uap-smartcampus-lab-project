# Generated manually for ToDo model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_eventregistration_department_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToDo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('assignment', 'Assignment'), ('exam', 'Exam')], default='assignment', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'To Do',
                'verbose_name_plural': 'To Dos',
            },
        ),
    ]
