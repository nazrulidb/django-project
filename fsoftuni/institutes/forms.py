from wagtail.admin.forms.models import WagtailAdminModelForm

from .models import Degree, CustomDocument, Institute
from wagtail.documents.forms import (
    BaseDocumentForm,
    get_document_base_form,
    get_document_form,
    get_document_multi_form,
)

class DocumentForm(BaseDocumentForm):
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = kwargs.pop('user')
        print(args)
        print(kwargs)
        print(f'USER {self.user}')
        print(self.initial)
        self.fields['collection'].disabled = True
        collection = self.fields['collection'].queryset
        print(collection.first())
        print(self.fields['institute'].choices)
        if not self.user.is_superuser:
            del self.fields['collection']
            institute = Institute.objects.filter(id=self.user.institute.id).first()
            self.fields['institute'].choices = [(institute.id, institute.name)]
     

    def save(self, commit=True):
        instance = super().save()
        print("DOCUMENT SAVE!")

class DegreeForm(WagtailAdminModelForm):
    class Meta:
        model = Degree
        fields = ("institute", "name", "code")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.for_user = kwargs.get("for_user")

        print("DEPT FORM!")

        if not self.for_user.is_superuser:
            print("IF MGA DIM ")
            self.initial = {"institute": self.for_user.institute}
            self.fields["institute"].disabled = True
