# coding: utf-8

from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.decorators import permission_required
from django.core import management
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import Context, Template
from django.utils import six
from django.utils.translation import ugettext, ugettext_lazy

from .models import Album, AlbumAccessPolicy, Photo, PhotoAccessPolicy


class SetAccessPolicyMixin(object):
    actions = ['set_access_policy', 'unset_access_policy']

    def set_access_policy(self, request, queryset):
        policy_model = {Album: AlbumAccessPolicy, Photo: PhotoAccessPolicy}[self.model]
        model_name = self.model._meta.model_name
        policy_model_name = policy_model._meta.model_name
        form_class = modelform_factory(
            policy_model,
            exclude=(model_name,),
            widgets={
                'users': FilteredSelectMultiple(ugettext("Users"), False),
                'groups': FilteredSelectMultiple(ugettext("Groups"), False),
            })

        if request.POST.get('set_access_policy'):
            form = form_class(request.POST)
            if form.is_valid():
                queryset = queryset.select_related('access_policy')
                # Check permissions
                has_add_perm = request.user.has_perm('gallery.add_%s' % policy_model_name)
                has_change_perm = request.user.has_perm('gallery.change_%s' % policy_model_name)
                for obj in queryset:
                    try:
                        obj.access_policy
                    except policy_model.DoesNotExist:
                        if not has_add_perm:
                            raise PermissionDenied
                    else:
                        if not has_change_perm:
                            raise PermissionDenied
                # Apply changes
                created, changed = 0, 0
                for obj in queryset:
                    try:
                        ap = obj.access_policy
                        changed += 1
                    except policy_model.DoesNotExist:
                        ap = policy_model.objects.create(**{model_name: obj})
                        created += 1
                    form_class(request.POST, instance=ap).save()
                message = ugettext("Successfully created %(created)d and "
                                   "changed %(changed)d access policies.")
                message = message % {'created': created, 'changed': changed}
                self.message_user(request, message)
                return HttpResponseRedirect(reverse('admin:gallery_%s_changelist' % model_name))
        else:
            form = form_class()
        context = {
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'opts': self.model._meta,
            'form': form,
            'media': self.media + form.media,
            'photos': Photo.objects.filter(album__in=queryset),
            'queryset': queryset,
            'title': ugettext("Set access policy"),
        }
        return render(request, 'admin/gallery/set_access_policy.html', context)

    set_access_policy.short_description = ugettext_lazy("Set access policy")

    def unset_access_policy(self, request, queryset):
        policy_model = {Album: AlbumAccessPolicy, Photo: PhotoAccessPolicy}[self.model]
        model_name = self.model._meta.model_name
        policy_model_name = policy_model._meta.model_name
        if request.POST.get('unset_access_policy'):
            queryset = queryset.select_related('access_policy')
            # Check permissions
            has_delete_perm = request.user.has_perm('gallery.delete_%s' % policy_model_name)
            for obj in queryset:
                try:
                    obj.access_policy
                except policy_model.DoesNotExist:
                    pass
                else:
                    if not has_delete_perm:
                        raise PermissionDenied
            # Apply changes
            deleted = 0
            for obj in queryset:
                try:
                    ap = obj.access_policy
                except policy_model.DoesNotExist:
                    pass
                else:
                    ap.delete()
                    deleted += 1
            message = ugettext("Successfully deleted %(deleted)d access policies.")
            message = message % {'deleted': deleted}
            self.message_user(request, message)
            return HttpResponseRedirect(reverse('admin:gallery_%s_changelist' % model_name))

        context = {
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'opts': self.model._meta,
            'photos': Photo.objects.filter(album__in=queryset),
            'queryset': queryset,
            'title': ugettext("Unset access policy"),
        }
        return render(request, 'admin/gallery/unset_access_policy.html', context)

    unset_access_policy.short_description = ugettext_lazy("Unset access policy")


class AccessPolicyInline(admin.StackedInline):
    filter_horizontal = ('groups', 'users')


class AlbumAccessPolicyInline(AccessPolicyInline):
    model = AlbumAccessPolicy


class AlbumAdmin(SetAccessPolicyMixin, admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (AlbumAccessPolicyInline,)
    list_display = ('display_name', 'date', 'category', 'public', 'groups', 'users', 'inherit')
    list_filter = ('category',)
    ordering = ('-date', '-name', '-dirpath', '-category')
    readonly_fields = ('dirpath',)
    search_fields = ('name', 'dirpath')

    def get_queryset(self, request):
        return (super(AlbumAdmin, self).get_queryset(request)
                .prefetch_related('access_policy__users')
                .prefetch_related('access_policy__groups'))

    def public(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            return access_policy.public
    public.boolean = True

    def groups(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            groups = access_policy.groups.all()
            return ', '.join(six.text_type(group) for group in groups)
        else:
            return '-'

    def users(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            users = access_policy.users.all()
            return ', '.join(six.text_type(user) for user in users)
        else:
            return '-'

    def inherit(self, obj):
        access_policy = obj.get_access_policy()
        if access_policy:
            return access_policy.inherit
    inherit.boolean = True

admin.site.register(Album, AlbumAdmin)


class PhotoAccessPolicyInline(AccessPolicyInline):
    model = PhotoAccessPolicy


class PhotoAdmin(SetAccessPolicyMixin, admin.ModelAdmin):
    date_hierarchy = 'date'
    inlines = (PhotoAccessPolicyInline,)
    list_display = ('display_name', 'date', 'preview', 'public', 'groups', 'users')
    # Since date is mandatory on albums, '-album_date' avoids showing photos
    # without date first on some databases (PostgreSQL).
    ordering = ('-album__date', '-date', '-filename')
    readonly_fields = ('filename',)
    search_fields = ('album__name', 'album__dirpath', 'filename')

    def get_urls(self):
        return [
            url(r'^scan/$', scan_photos, name='gallery_scan_photos'),
        ] + super(PhotoAdmin, self).get_urls()

    def get_queryset(self, request):
        return (super(PhotoAdmin, self).get_queryset(request)
                .prefetch_related('access_policy__users')
                .prefetch_related('access_policy__groups')
                .prefetch_related('album__access_policy__users')
                .prefetch_related('album__access_policy__groups'))

    preview_template = Template("""
<a href="{{ photo.get_absolute_url }}">
<img src="{% url 'gallery:photo-resized' preset='thumb' pk=photo.pk %}"
     width="128" height="128" alt="{{ photo }}" />
</a>""")

    def preview(self, obj):
        return self.preview_template.render(Context({'photo': obj}))
    preview.allow_tags = True

    def public(self, obj):
        access_policy = obj.get_effective_access_policy()
        if access_policy:
            return access_policy.public
    public.boolean = True

    def groups(self, obj):
        access_policy = obj.get_effective_access_policy()
        if access_policy:
            return ', '.join(six.text_type(group) for group in access_policy.groups.all())
        else:
            return '-'

    def users(self, obj):
        access_policy = obj.get_effective_access_policy()
        if access_policy:
            return ', '.join(six.text_type(user) for user in access_policy.users.all())
        else:
            return '-'

admin.site.register(Photo, PhotoAdmin)


@permission_required('gallery.scan')
def scan_photos(request):
    if request.method == 'POST':
        stdout, stderr = six.StringIO(), six.StringIO()
        management.call_command('scanphotos', stdout=stdout, stderr=stderr)
        for line in stdout.getvalue().splitlines():
            messages.info(request, line)
        for line in stderr.getvalue().splitlines():
            messages.error(request, line)
        return HttpResponseRedirect(reverse('admin:gallery_scan_photos'))
    context = {
        'app_label': 'gallery',
        'title': ugettext("Scan photos"),
    }
    return render(request, 'admin/gallery/scan_photos.html', context)
