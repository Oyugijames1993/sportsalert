from django import forms
from django.forms import inlineformset_factory

from .models import (
    Watch,
    WatchParameter,
)

class WatchForm(forms.ModelForm):

    class Meta:
        model = Watch

        fields = [
            "sport",
            "match_id",
            "home_team",
            "away_team",
            "league",
            "monitoring_start",
            "active",
        ]

        widgets = {
            "sport": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "match_id": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "home_team": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "away_team": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "league": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "monitoring_start": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),

            "active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),
        }


class WatchParameterForm(forms.ModelForm):

    class Meta:
        model = WatchParameter

        fields = [
            "parameter",
            "baseline",
            "threshold",
        ]

        widgets = {
            "parameter": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "baseline": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Baseline",
                }
            ),

            "threshold": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Threshold",
                }
            ),
        }

    def clean_baseline(self):

        baseline = self.cleaned_data.get(
            "baseline"
        )

        if (
            baseline is not None
            and baseline < 0
        ):
            raise forms.ValidationError(
                "Baseline cannot be negative."
            )

        return baseline

    def clean_threshold(self):

        threshold = self.cleaned_data.get(
            "threshold"
        )

        if (
            threshold is not None
            and threshold <= 0
        ):
            raise forms.ValidationError(
                "Threshold must be greater than 0."
            )

        return threshold


WatchParameterFormSet = inlineformset_factory(
    Watch,
    WatchParameter,
    form=WatchParameterForm,
    extra=1,
    can_delete=True,
)