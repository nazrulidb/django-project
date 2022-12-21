from wagtail.users.views.groups import GroupViewSet as WagtailGroupViewSet
from .forms import GroupForm


class GroupViewSet(WagtailGroupViewSet):
    def get_form_class(self, for_update=False):
        return GroupForm
