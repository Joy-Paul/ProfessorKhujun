from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

# আপনার তৈরি করা মডেলগুলো
from .models import Professor, Review, University, StudentProfile, ProfessorUpdateRequest, ProfileClaimRequest, Bookmark, Report

# ==========================================
# ১. হোমপেজ ভিউ
# ==========================================
def home(request):
    universities = University.objects.all()
    countries = University.objects.values_list('country', flat=True).distinct()
    departments = Professor.objects.values_list('department', flat=True).distinct()

    query = request.GET.get('q')
    uni_id = request.GET.get('university')
    country_name = request.GET.get('country')
    dept_name = request.GET.get('department')

    # শুধুমাত্র ভেরিফাইড প্রফেসরদের দেখানো হবে এবং লেটেস্টরা আগে আসবে
    professors = Professor.objects.filter(is_verified=True).order_by('-id')

    # ফিল্টারিং লজিক
    if query:
        professors = professors.filter(
            Q(name__icontains=query) | Q(research_area__icontains=query)
        )
    if uni_id:
        professors = professors.filter(university_id=uni_id)
    if country_name:
        professors = professors.filter(university__country=country_name)
    if dept_name:
        professors = professors.filter(department=dept_name)

    return render(request, 'home.html', {
        'professors': professors,
        'universities': universities,
        'countries': countries,
        'departments': departments,
        'selected_uni': uni_id,
        'selected_country': country_name,
        'selected_dept': dept_name,
        # --- এই নতুন লাইনটি যোগ করুন ---
        'query': query,
    })

# ==========================================
# ২. প্রফেসর ডিটেইল ভিউ
# ==========================================
def professor_detail(request, pk):
    professor = get_object_or_404(Professor, pk=pk, is_verified=True)
    reviews = professor.reviews.all().order_by('-created_at')
    top_reviews = professor.reviews.filter(rating__gte=4).order_by('-rating', '-created_at')[:10]
    
    is_bookmarked = False
    has_reviewed = False # নতুন: চেক করবে ইউজার আগে রিভিউ দিয়েছে কি না
    
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, professor=professor).exists()
        has_reviewed = Review.objects.filter(user=request.user, professor=professor).exists()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        student = getattr(request.user, 'student_profile', None)
        if student and student.is_verified:
            # অ্যান্টি-স্প্যাম লজিক: একটির বেশি রিভিউ দেওয়া যাবে না
            if has_reviewed:
                messages.error(request, "আপনি আগে থেকেই এই প্রফেসরের প্রোফাইলে একটি রিভিউ দিয়েছেন।")
            else:
                rating = request.POST.get('rating')
                comment = request.POST.get('comment')
                Review.objects.create(professor=professor, user=request.user, rating=rating, comment=comment)
                messages.success(request, "আপনার রিভিউ সফলভাবে সাবমিট হয়েছে!")
        else:
            messages.error(request, "রিভিউ দেওয়ার জন্য আপনার স্টুডেন্ট আইডি অ্যাডমিন দ্বারা ভেরিফাইড হতে হবে।")
        return redirect('professor_detail', pk=pk)

    return render(request, 'professor_detail.html', {
        'professor': professor,
        'reviews': reviews,
        'top_reviews': top_reviews,
        'is_bookmarked': is_bookmarked,
        'has_reviewed': has_reviewed # এটি টেমপ্লেটে পাঠানো হলো
    })
# ==========================================
# ৩. সাইনআপ ভিউ
# ==========================================
def signup_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # প্রফেসরদের জন্য .edu ইমেইল চেক
        if role == 'professor' and not (email.endswith('.edu') or email.endswith('.edu.bd')):
            messages.error(request, "প্রফেসর অ্যাকাউন্ট খুলতে অবশ্যই .edu বা .edu.bd ইমেইল লাগবে।")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "এই ইউজারনেমটি আগে থেকেই ব্যবহার করা হচ্ছে।")
            return redirect('signup')

        user = User.objects.create_user(username=username, email=email, password=password)
        
        if role == 'student':
            StudentProfile.objects.create(user=user)
            messages.success(request, "অ্যাকাউন্ট তৈরি হয়েছে! অ্যাডমিন ভেরিফাই করলে রিভিউ দিতে পারবেন।")
            login(request, user)
            return redirect('home')
            
        elif role == 'professor':
            messages.success(request, "অ্যাকাউন্ট তৈরি হয়েছে। ড্যাশবোর্ড থেকে আপনার বিস্তারিত তথ্য সাবমিট করুন।")
            login(request, user)
            return redirect('professor_dashboard')
            
    return render(request, 'auth/signup.html')

# ==========================================
# ৪. লগইন ও লগআউট ভিউ
# ==========================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password  = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # যদি ইমেইল .edu দিয়ে শেষ হয় অথবা তার প্রফেসর প্রোফাইল থাকে, তাকে ড্যাশবোর্ডে পাঠাবে
            if user.email.endswith('.edu') or user.email.endswith('.edu.bd') or hasattr(user, 'professor_profile'):
                return redirect('professor_dashboard')
            return redirect('home') # স্টুডেন্ট হলে হোমপেজে
        else:
            messages.error(request, "ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে।")
            
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# ==========================================
# ৫. প্রফেসর ড্যাশবোর্ড (প্রোফাইল তৈরি + আপডেট রিকোয়েস্ট)
# ==========================================
@login_required
def professor_dashboard(request):
    if not (request.user.email.endswith('.edu') or request.user.email.endswith('.edu.bd') or hasattr(request.user, 'professor_profile')):
        messages.error(request, "এই পেজটি শুধুমাত্র প্রফেসরদের জন্য।")
        return redirect('home')

    professor = getattr(request.user, 'professor_profile', None)
    
    # ইউজার কোনো প্রোফাইল ক্লেইম করার রিকোয়েস্ট পাঠিয়েছে কি না চেক করা
    has_pending_claim = ProfileClaimRequest.objects.filter(user=request.user, is_approved=False).exists()

    if request.method == 'POST':
        action = request.POST.get('action') # ফর্ম থেকে অ্যাকশন ধরা হচ্ছে

        if action == 'claim_profile':
            prof_id = request.POST.get('professor_id')
            selected_prof = get_object_or_404(Professor, id=prof_id)
            ProfileClaimRequest.objects.create(user=request.user, professor=selected_prof)
            messages.success(request, "প্রোফাইল ক্লেইম রিকোয়েস্ট পাঠানো হয়েছে! অ্যাডমিন ভেরিফাই করলে আপনি প্রোফাইলের অ্যাক্সেস পাবেন।")
            return redirect('professor_dashboard')

        elif action == 'create_profile' and not professor:
            name = request.POST.get('name')
            uni_id = request.POST.get('university')
            dept = request.POST.get('department')
            research = request.POST.get('research_area')
            email = request.POST.get('email')
            image = request.FILES.get('image')

            Professor.objects.create(
                user=request.user, name=name, university_id=uni_id,
                department=dept, research_area=research, email=email,
                image=image, is_verified=False
            )
            messages.success(request, "আপনার প্রোফাইল সাবমিট করা হয়েছে! অ্যাডমিন ভেরিফাই করলে এটি সাইটে দেখা যাবে।")
            return redirect('professor_dashboard')

        elif action == 'update_request' and professor:
            requested_changes = request.POST.get('changes')
            if requested_changes:
                ProfessorUpdateRequest.objects.create(professor=professor, requested_changes=requested_changes)
                messages.success(request, "আপনার আপডেট রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে।")
                return redirect('professor_dashboard')

    universities = University.objects.all()
    # যেসব প্রফেসরের প্রোফাইলের সাথে কোনো ইউজার লিঙ্ক করা নেই, শুধু তাদেরকেই ক্লেইম করা যাবে
    unclaimed_professors = Professor.objects.filter(user__isnull=True, is_verified=True)
    update_requests = ProfessorUpdateRequest.objects.filter(professor=professor).order_by('-created_at') if professor else None
    
    return render(request, 'auth/professor_dashboard.html', {
        'professor': professor,
        'universities': universities,
        'unclaimed_professors': unclaimed_professors,
        'update_requests': update_requests,
        'has_pending_claim': has_pending_claim
    })

@login_required
def toggle_bookmark(request, prof_id):
    professor = get_object_or_404(Professor, id=prof_id)
    # বুকমার্ক থাকলে ডিলিট করবে, না থাকলে তৈরি করবে
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, professor=professor)
    
    if not created:
        bookmark.delete()
        messages.info(request, "প্রোফাইলটি বুকমার্ক থেকে সরানো হয়েছে।")
    else:
        messages.success(request, "প্রোফাইলটি সফলভাবে সেভ করা হয়েছে।")
    
    return redirect('professor_detail', pk=prof_id)

@login_required
def student_dashboard(request):
    # স্টুডেন্টের সেভ করা সব প্রফেসরদের লিস্ট আনা
    saved_profs = Bookmark.objects.filter(user=request.user).select_related('professor')
    return render(request, 'auth/student_dashboard.html', {'saved_profs': saved_profs})

@login_required
def update_application_status(request, bookmark_id):
    if request.method == 'POST':
        bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
        new_status = request.POST.get('status')
        if new_status:
            bookmark.status = new_status
            bookmark.save()
            messages.success(request, f"{bookmark.professor.name}-এর স্ট্যাটাস আপডেট করা হয়েছে!")
    return redirect('student_dashboard')

# ==========================================
# Stripe API Key সেট করা (এই লাইনটি যোগ করুন)
# ==========================================
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request):
    if request.method == 'POST':
        # ইউজার ফর্ম থেকে যে অ্যামাউন্ট সিলেক্ট করবে (ডিফল্ট $5)
        amount = int(request.POST.get('amount', 5)) * 100 # Stripe সেন্ট (Cents) এ হিসাব করে
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Support Professorkhujun',
                            'description': 'আপনার এই অনুদান আমাদের সার্ভার মেইনটেইন করতে সাহায্য করবে।',
                        },
                        'unit_amount': amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                
                # --- ঠিক এখানেই পরিবর্তনটি করা হয়েছে ---
                success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                # ---------------------------------------
                
                cancel_url=request.build_absolute_uri(reverse('home')),
            )
            # Stripe-এর নিজস্ব সিকিউর পেমেন্ট পেজে রিডাইরেক্ট করে দেবে
            return redirect(checkout_session.url, code=303)
        # except Exception as e:
        #     messages.error(request, "পেমেন্ট গেটওয়েতে একটি সমস্যা হয়েছে।")
        #     return redirect('home')
        except Exception as e:
            # টার্মিনালে এররটি প্রিন্ট করবে
            print(f"Stripe Error: {e}") 
            # ওয়েবসাইটে ইউজারের কাছে আসল এররটি দেখাবে
            messages.error(request, f"পেমেন্ট শুরু করতে সমস্যা হয়েছে: {e}") 
            # return redirect('home')
    return redirect('home')

def payment_success(request):
    # Stripe থেকে সেশন আইডি ধরে ইউজারের ইমেইল বের করা
    session_id = request.GET.get('session_id')
    user_email = None
    
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            user_email = session.customer_details.email
        except Exception:
            pass

    # যদি ইউজারের ইমেইল পাওয়া যায়, তবে তাকে থ্যাংক ইউ ইমেইল পাঠানো
    if user_email:
        subject = 'Thank You for Supporting Professorkhujun! 💙'
        
        # HTML ইমেইল টেমপ্লেট রেন্ডার করা (আমরা নিচে এটি তৈরি করব)
        html_message = render_to_string('emails/donation_thank_you.html')
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject,
                plain_message,
                settings.EMAIL_HOST_USER,
                [user_email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            # ইমেইল পাঠাতে কোনো সমস্যা হলে সেটি ইগনোর করবে
            print(f"Email error: {e}")

    messages.success(request, "আপনার অনুদানের জন্য অসংখ্য ধন্যবাদ! আপনাকে একটি কনফার্মেশন ইমেইল পাঠানো হয়েছে।")
    return redirect('home')

def university_deadlines(request):
    query = request.GET.get('q', '')
    # সব ইউনিভার্সিটি আনা হচ্ছে এবং নামের ক্রমানুসারে (A-Z) সাজানো হচ্ছে
    universities = University.objects.all().order_by('name')
    
    if query:
        # যদি ইউজার কিছু লিখে সার্চ করে, তবে নামের সাথে মিলিয়ে ফিল্টার করবে
        universities = universities.filter(name__icontains=query)
        
    return render(request, 'university_deadlines.html', {
        'universities': universities,
        'query': query
    })


def report_professor(request, prof_id):
    if request.method == 'POST':
        professor = get_object_or_404(Professor, id=prof_id)
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        user = request.user if request.user.is_authenticated else None
        
        Report.objects.create(
            professor=professor, 
            user=user, 
            issue_type=issue_type, 
            description=description
        )
        messages.success(request, "রিপোর্ট সাবমিট করার জন্য ধন্যবাদ! অ্যাডমিন খুব দ্রুত এটি চেক করে দেখবে।")
    return redirect('professor_detail', pk=prof_id)