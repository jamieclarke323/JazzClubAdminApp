from django import forms


class ShoppingForm(forms.Form):
    name = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'placeholder': 'Milk'}))
    section = forms.CharField(max_length=80, required=False, widget=forms.TextInput(attrs={'placeholder': 'Fridge'}))
    list_type = forms.ChoiceField(choices=[('groceries', 'Groceries'), ('other', 'Other shopping')])
    note = forms.CharField(max_length=260, required=False, widget=forms.TextInput(attrs={'placeholder': 'Optional note'}))
