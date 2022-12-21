# models.py

from django.db import models
from django_jsonform.models.fields import JSONField


class ShoppingList(models.Model):
    ITEMS_SCHEMA = {
        'type': 'array', # a list which will contain the items
        'items': {
            'type': 'string' # items in the array are strings
        }
    }

    items = JSONField(schema=ITEMS_SCHEMA)
    date_created = models.DateTimeField(auto_now_add=True)

def callable_schema(instance=None):
    # instance will be None while creating new object

    if instance:
        # ... do something with the instance ...
    else:
        # ... do something else ...
    return schema


class MyModel(models.Model):
    my_field = JSONField(schema=callable_schema)


...

# admin.py

# create a custom modelform
class MyModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # manually set the current instance on the widget
        self.fields['my_field'].widget.instance = self.instance


# set the form on the admin class
class MyAdmin(admin.ModelAdmin):
    form = MyModelForm


admin.site.register(MyModel, MyAdmin)
# class HomePage(Page):
#     pass
