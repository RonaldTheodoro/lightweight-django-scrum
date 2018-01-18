from datetime import date

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy

from rest_framework import serializers
from rest_framework.reverse import reverse

from . import models


User = get_user_model()


class SprintSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = models.Sprint
        fields = ('id', 'name', 'description', 'end', 'links', )

    def get_links(self, obj):
        request = self.context['request']
        return {
            'self': reverse(
                'sprint-detail',
                kwargs={'pk': obj.pk},
                request=request
            ),
            'tasks': reverse(
                'task-list',
                request=request
            ) + f'?sprint={obj.pk}',
        }

    def validate_end(self, value):
        new = not self.instance
        changed = self.instance and self.instance.end != end_date

        if (new or changed) and (value < date.today()):
            msg = ugettext_lazy('End date cannot be in the past')
            raise serializers.ValidationError(msg)
        
        return value


class TaskSerializer(serializers.ModelSerializer):
    assigned = serializers.SlugRelatedField(
        slug_field=User.USERNAME_FIELD,
        required=False,
        queryset=User.objects.all()
    )
    status_display = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()

    class Meta:
        model = models.Task
        fields = (
            'id', 'name', 'description', 'sprint', 'status', 'status_display', 'order', 'assigned', 'started', 'due', 'completed', 'links',
        )

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_links(self, obj):
        request = self.context['request']
        links = {
            'self': reverse(
                'task-detail',
                kwargs={'pk': obj.pk},
                request=request
            ),
            'sprint': None,
            'assigned': None,
        }
        if obj.sprint_id:
            links['assigned'] = reverse(
                'sprint-detail',
                kwargs={'pk': obj.sprint_id},
                request=request
            )
        if obj.assigned:
            links['assigned'] = reverse(
                'user-detail',
                kwargs={User.USERNAME_FIELD: obj.assigned},
                request=request
            )
        return links

    def validate_sprint(self, value):
        if self.instance and self.instance.pk:
            if value != self.instance.sprint:
                if self.instance.status == models.Task.STATUS.DONE:
                    msg = ugettext_lazy(
                        'Cannot change the sprint of a completd task'
                    )
                    raise serializers.ValidationError(msg)
                if value and value.end < date.today():
                    msg = ugettext_lazy(
                        'Cannot assign tasks to pass sprints'
                    )
                    raise serializers.ValidationError(msg)
            else:
                if value and value.end < date.today():
                    msg = ugettext_lazy(
                        'Cannot add tasks to pass sprints'
                    )
                    raise serializers.ValidationError(msg)
        return value

    def validate(self, data):
        sprint = data.get('sprint')
        status = data.get('status', models.Task.STATUS.TODO)
        started = data.get('started')
        completed = data.get('completed')

        if not sprint and (status != models.Task.STATUS.TODO):
            msg = ugettext_lazy(
                'Backlog tasks must have "Not Started" status'
            )
            raise serializers.ValidationError(msg)

        if started and (status == models.Task.STATUS.TODO):
            msg = ugettext_lazy(
                'Started date cannot be set for not started tasks'
            )
            raise serializers.ValidationError(msg)

        if completed and (status != models.Task.STATUS.DONE):
            msg = ugettext_lazy(
                'Completed date cannot be set for uncompleted tasks'
            )
            raise serializers.ValidationError(msg)

        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ('id', User.USERNAME_FIELD, 'full_name', 'is_active', )

    def get_links(self, obj):
        request = self.context['request']
        username = obj.get_username()
        return {
            'self': reverse(
                'user-detail',
                kwargs={User.USERNAME_FIELD: username},
                request=request
            ),
            'tasks': reverse(
                'task-list',
                request=request
            ) + f'?assigned={username}'
        }
