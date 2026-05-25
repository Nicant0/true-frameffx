from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, Submit
from .models import Teaching


class TeachingForm(forms.ModelForm):
    class Meta:
        model = Teaching
        exclude = ("fecha_creacion",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Fieldset(
                "Datos Teaching",
                Row(
                    Column("title", css_class="col-md-6"),
                ),
                Row(
                    Column("price", css_class="col-md-4"),
                    Column("duracion_min", css_class="col-md-4"),
                    Column("estado", css_class="col-md-4"),
                ),
                Row(
                    Column("description", css_class="col-md-12"),
                ),
                Row(
                    Column("start_at", css_class="col-md-6"),
                    Column("end_at", css_class="col-md-6"),
                ),
            ),
            Submit("submit", "Guardar", css_class="btn btn-primary"),
        )

    def clean(self):
        cleaned_data = super().clean()
        start_at = cleaned_data.get("start_at")
        end_at = cleaned_data.get("end_at")
        duracion_min = cleaned_data.get("duracion_min")
        price = cleaned_data.get("price")

        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "La fecha de fin debe ser mayor que la de inicio.")

        if duracion_min is not None and duracion_min <= 0:
            self.add_error("duracion_min", "La duracion debe ser mayor que cero.")

        if price is not None and price < 0:
            self.add_error("price", "El precio no puede ser negativo.")

        return cleaned_data
