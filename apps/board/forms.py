import django_filters

from django.contrib.auth import get_user_model

from . import models


User = get_user_model()


class NullFilter(django_filters.BooleanFilter):

    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{f'{self.name}__isnull': value})
        return qs


class SprintTask(django_filters.FilterSet):
    end_min = django_filters.DateFilter(name='end', lookup_expr='gte')
    end_max = django_filters.DateFilter(name='end', lookup_expr='lte')

    class Meta:
        model = models.Sprint
        fields = ('end_min', 'end_max', )


class TaskFilter(django_filters.FilterSet):
    backlog = NullFilter(name='sprint')

    class Meta:
        model = models.Task
        fields = ('sprint', 'status', 'assigned', 'backlog', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['assigned'].extra.update(
            {'to_field_name': User.USERNAME_FIELD}
        )