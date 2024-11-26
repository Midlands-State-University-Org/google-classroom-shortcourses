from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from .models import Course, CourseImage

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'price', 'startdate']  

        widgets = {
            'startdate': forms.DateInput(attrs={
                'type': 'date',  
                'class': 'form-input rounded-md border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            'name',
            'description',
            'price',
            'startdate',  
            Submit('submit', 'Create Class', css_class="bg-blue-500 text-white")
        )

class CourseImageForm(forms.ModelForm):
    class Meta:
        model = CourseImage
        fields = ['imagepath']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            'imagepath',
            Submit('submit', 'Upload Image', css_class="bg-green-500 text-white")
        )
