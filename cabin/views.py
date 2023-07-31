from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.temp import NamedTemporaryFile
from django.shortcuts import render
from django.http import HttpResponse

from jigger.models import Campaign

from .forms import EngageForm, CeaseForm
from .tasks import enqueue_enroll

# Create your views here.
@staff_member_required
def engage(request):

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = EngageForm(request.POST, request.FILES)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            #book_instance.due_back = form.cleaned_data['renewal_date']
            #book_instance.save()
            tmpfile = NamedTemporaryFile(delete=False)
            for chunk in form.cleaned_data['contacts'].chunks():
                tmpfile.write(chunk)

            enqueue_enroll(tmpfile.name, form.cleaned_data['campaign'], form.cleaned_data['start_at'].isoformat(), form.cleaned_data['re_init'])

            # redirect to a new URL:
            return HttpResponse('Operation queued.')
            #return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form
    else:
        #proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = EngageForm() #initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
    }

    return render(request, 'engage.html', context)


@staff_member_required
def cease(request):

    display_status = False
    campaign = None

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = CeaseForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)

            try:
                campaign = Campaign.objects.get(pk=form.cleaned_data['campaign'])
            except:
                display_status = "Unknown"

            if campaign:
                if 'cease' in request.POST:
                    campaign.ceased = True
                    campaign.save()
                elif 'resume' in request.POST:
                    campaign.ceased = False
                    campaign.save()

                display_status = "Ceased" if campaign.ceased else "Running"

    # If this is a GET (or any other method) create the default form
    else:
        form = CeaseForm()

    context = {
        'status': display_status,
        'form': form,
    }

    return render(request, 'cease.html', context)
