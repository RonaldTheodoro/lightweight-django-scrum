import hashlib

import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.views import generic

from rest_framework import authentication, filters, permissions, viewsets
from rest_framework.renderers import JSONRenderer

from . import forms, models, serializers

User = get_user_model()


class Index(generic.TemplateView):
    template_name = 'board/index.html'


class UpdateHookMixin:

    def _build_hook_url(self, obj):
        if isinstance(obj, User):
            model = 'user'
        else:
            model = obj.__class__.__name__.lower()

        protocol = 'https' if settings.WATERCOOLER_SECURE else 'http'
        server = settings.WATERCOOLER_SERVER

        return f'{protocol}://{server}/{model}/{obj.pk}'

    def _send_hook_request(self, obj, method):
        url = self._build_hook_url(obj)
        if method in ('POST', 'PUT', ):
            serializer = self.get_serializer(obj)
            renderer = JSONRenderer()
            context = {'request': self.request}
            body = renderer.render(serializer.data, renderer_context=context)
        else:
            body = None

        headers = {
            'content-type': 'application/json',
            'X-Signature': self._build_hook_signature(method, url, body),
        }

        try:
            response = requests.request(
                method,
                url,
                data=body,
                timeout=0.5,
                headers=headers
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.RequestException:
            pass

    def _build_hook_signature(self, method, url, body):
        signer = TimestampSigner(settings.WATERCOOLER_SECRET_KEY)
        method = method.lower()
        body = hashlib.sha256(body or b'').hexdigest()
        value = f'{method}:{url}:{body}'
        return signer.sign(value)

    def post_save(self, obj, create=False):
        method = 'POST' if create else 'PUT'
        self._send_hook_request(obj, method)

    def pre_delete(self, obj):
        self._send_hook_request(obj, 'DELETE')


class SprintViewSet(UpdateHookMixin, viewsets.ModelViewSet):
    queryset = models.Sprint.objects.order_by('end')
    serializer_class = serializers.SprintSerializer
    filter_class = forms.SprintTask
    search_fields = ('name', )
    ordering_fields = ('end', 'description', )


class TaskViewSet(UpdateHookMixin, viewsets.ModelViewSet):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_class = forms.TaskFilter
    search_fields = ('name', 'description', )
    ordering_fields = ('name', 'order', 'started', 'due', 'completed', )


class UserViewSet(UpdateHookMixin, viewsets.ReadOnlyModelViewSet):
    lookup_field = User.USERNAME_FIELD
    lookup_url_kwarg = User.USERNAME_FIELD
    queryset = User.objects.order_by(User.USERNAME_FIELD)
    serializer_class = serializers.UserSerializer
    search_fields = (User.USERNAME_FIELD, )
