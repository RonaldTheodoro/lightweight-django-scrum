from django.contrib.auth import get_user_model

from rest_framework import authentication, permissions, viewsets

from . import forms, models, serializers

User = get_user_model()


class SprintViewSet(viewsets.ModelViewSet):
    queryset = models.Sprint.objects.order_by('end')
    serializer_class = serializers.SprintSerializer
    filter_class = forms.SprintTask
    search_fields = ('name', )
    ordering_fields = ('end', 'description', )


class TaskViewSet(viewsets.ModelViewSet):
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_class = forms.TaskFilter
    search_fields = ('name', 'description', )
    ordering_fields = ('name', 'order', 'started', 'due', 'completed', )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = User.USERNAME_FIELD
    lookup_url_kwarg = User.USERNAME_FIELD
    queryset = User.objects.order_by(User.USERNAME_FIELD)
    serializer_class = serializers.UserSerializer
    search_fields = (User.USERNAME_FIELD, )
