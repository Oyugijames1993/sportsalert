from django import forms
from django.forms import inlineformset_factory

from .models import (
    Watch,
    WatchParameter,
    StatAlertRule,
    StatOddsModel,
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

class StatAlertRuleForm(forms.ModelForm):
    class Meta:
        model = StatAlertRule
        fields = [
            "stat_type",
            "team_scope",
            "mode",
            "silence_gap_minutes",
            "burst_count",
            "burst_window_minutes",
            "expected_total",
            "active",
        ]
        widgets = {
            "stat_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "team_scope": forms.Select(
                attrs={"class": "form-select"}
            ),
            "mode": forms.Select(
                attrs={"class": "form-select", "onchange": "toggleModeFields(this)"}
            ),
            "silence_gap_minutes": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g. 10"}
            ),
            "burst_count": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g. 5"}
            ),
            "burst_window_minutes": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g. 10"}
            ),
            "expected_total": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "e.g. 10"}
            ),
            "active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get("mode")
        silence_gap_minutes = cleaned_data.get("silence_gap_minutes")
        burst_count = cleaned_data.get("burst_count")
        burst_window_minutes = cleaned_data.get("burst_window_minutes")

        if mode == "silence" and not silence_gap_minutes:
            raise forms.ValidationError(
                "Silence mode requires a gap (minutes) value."
            )
        if mode == "burst" and not (burst_count and burst_window_minutes):
            raise forms.ValidationError(
                "Burst mode requires both a count and a window (minutes)."
            )
        return cleaned_data


StatAlertRuleFormSet = inlineformset_factory(
    Watch,
    StatAlertRule,
    form=StatAlertRuleForm,
    extra=1,
    can_delete=True,
)


class StatOddsModelForm(forms.ModelForm):
    class Meta:
        model = StatOddsModel
        fields = [
            "stat_type",
            "mu_0",
            "dispersion_r",
            "overround",
            "confidence_threshold",
        ]
        widgets = {
            "stat_type": forms.Select(
                attrs={"class": "form-select odds-stat-type", "onchange": "fillDefaultDispersion(this)"}
            ),
            "mu_0": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 20.36"}
            ),
            "dispersion_r": forms.NumberInput(
                attrs={"class": "form-control odds-dispersion-r", "step": "0.01", "placeholder": "leave blank for default"}
            ),
            "overround": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 1.10"}
            ),
            "confidence_threshold": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "placeholder": "e.g. 0.80"}
            ),
        }


StatOddsModelFormSet = inlineformset_factory(
    Watch,
    StatOddsModel,
    form=StatOddsModelForm,
    extra=1,
    can_delete=True,
)
