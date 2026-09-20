from django.contrib.auth.views import LoginView

from .forms import SignInForm


class SignInView(LoginView):
    template_name = "registration/login.html"
    authentication_form = SignInForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session.set_expiry(1209600 if form.cleaned_data["remember_me"] else 0)
        return response
