from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistrationForm


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)  # já loga automaticamente após criar a conta
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'jogadores/register.html', {'form': form})