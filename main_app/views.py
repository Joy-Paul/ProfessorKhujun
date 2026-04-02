from django.shortcuts import render
from .models import Professor, University
from django.db.models import Q

def home(request):
    # সব ইউনিভার্সিটি এবং প্রফেসর নিয়ে আসা
    universities = University.objects.all()
    query = request.GET.get('q')
    uni_filter = request.GET.get('university')

    professors = Professor.objects.all()

    if query:
        professors = professors.filter(
            Q(name__icontains=query) | 
            Q(research_area__icontains=query) |
            Q(department__icontains=query)
        )
    
    if uni_filter:
        professors = professors.filter(university__id=uni_filter)

    context = {
        'professors': professors,
        'universities': universities,
    }
    return render(request, 'home.html', context)