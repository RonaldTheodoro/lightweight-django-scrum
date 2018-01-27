from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy

from model_utils import Choices


class Sprint(models.Model):
    name = models.CharField('name', max_length=100, blank=True, default='')
    description = models.TextField('description', blank=True, default='')
    end = models.DateField('end', unique=True)

    def __str__(self):
        return self.name or ugettext_lazy(f'Spring ending {self.end}')


class Task(models.Model):
    STATUS = Choices(
        (1, 'TODO', ugettext_lazy('Not Started')),
        (2, 'IN_PROGRESS', ugettext_lazy('In Progress')),
        (3, 'TESTING', ugettext_lazy('Testing')),
        (4, 'DONE', ugettext_lazy('Done')),
    )
    name = models.CharField('name', max_length=100)
    description = models.TextField('description', blank=True, default='')
    sprint = models.ForeignKey(
        'Sprint',
        blank=True,
        default='',
        verbose_name='sprint'
    )
    status = models.SmallIntegerField(
        'status',
        choices=STATUS,
        default=STATUS.TODO
    )
    order = models.SmallIntegerField('order', default=0)
    assigned = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        verbose_name='assigned'
    )
    started = models.DateField('started', blank=True, null=True)
    due = models.DateField('due', blank=True, null=True)
    completed = models.DateField('completed', blank=True, null=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name