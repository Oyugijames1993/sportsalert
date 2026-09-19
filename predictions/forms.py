from django import forms
from .models import CoachProfile


class CoachProfileForm(forms.ModelForm):
    class Meta:
        model = CoachProfile
        fields = "__all__"
        widgets = {
            "coach_id": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional API coach ID",
                }
            ),
            "coach_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Coach name",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ["coach_id", "coach_name"]:
                continue

            field.widget.attrs.update({
                "class": "form-control",
                "step": "0.01",
            })

        self.fields["ppda_home"].label = "PPDA — Home"
        self.fields["ppda_away"].label = "PPDA — Away"

        self.fields["transition_to_shot_seconds_home"].label = (
            "Transition to Shot — Home (seconds)"
        )
        self.fields["transition_to_shot_seconds_away"].label = (
            "Transition to Shot — Away (seconds)"
        )
