# Generated by Django 1.11.16 on 2018-08-17 20:28
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=100)),
                ('dirpath', models.CharField(max_length=200, verbose_name='directory path')),
                ('date', models.DateField()),
                ('name', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'verbose_name': 'album',
                'verbose_name_plural': 'albums',
                'ordering': ('date', 'name', 'dirpath', 'category'),
            },
        ),
        migrations.CreateModel(
            name='AlbumAccessPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public', models.BooleanField(default=False, verbose_name='is public')),
                ('inherit', models.BooleanField(blank=True, default=True, verbose_name='photos inherit album access policy')),
                ('album', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='access_policy', to='gallery.Album')),
                ('groups', models.ManyToManyField(blank=True, to='auth.Group', verbose_name='authorized groups')),
                ('users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='authorized users')),
            ],
            options={
                'verbose_name': 'album access policy',
                'verbose_name_plural': 'album access policies',
            },
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=100, verbose_name='file name')),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('album', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gallery.Album')),
            ],
            options={
                'verbose_name': 'photo',
                'verbose_name_plural': 'photos',
                'ordering': ('date', 'filename'),
                'permissions': (('view', 'Can see all photos'), ('scan', 'Can scan the photos directory')),
            },
        ),
        migrations.CreateModel(
            name='PhotoAccessPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public', models.BooleanField(default=False, verbose_name='is public')),
                ('groups', models.ManyToManyField(blank=True, to='auth.Group', verbose_name='authorized groups')),
                ('photo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='access_policy', to='gallery.Photo')),
                ('users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='authorized users')),
            ],
            options={
                'verbose_name': 'photo access policy',
                'verbose_name_plural': 'photo access policies',
            },
        ),
        migrations.AlterUniqueTogether(
            name='album',
            unique_together=set([('dirpath', 'category')]),
        ),
        migrations.AlterUniqueTogether(
            name='photo',
            unique_together=set([('album', 'filename')]),
        ),
    ]
