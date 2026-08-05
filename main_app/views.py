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
from django.urls import reverse
from django.contrib import messages
from datetime import date, datetime


import requests

from .models import Professor, Review, University, StudentProfile, ProfessorUpdateRequest, ProfileClaimRequest, Bookmark, Report, OTPVerification, SubjectDeadline, Article

def home(request):
    universities = University.objects.all()
    countries = University.objects.values_list('country', flat=True).distinct()
    departments = Professor.objects.values_list('department', flat=True).distinct()

    # ডাটাবেস থেকে Community & Resources এর জন্য সর্বশেষ ৩টি আর্টিকেল ফেচ করা হচ্ছে
    articles = Article.objects.all().order_by('-created_at')[:3]

    query = request.GET.get('q')
    uni_id = request.GET.get('university')
    country_name = request.GET.get('country')
    dept_name = request.GET.get('department')

    professors = Professor.objects.filter(is_verified=True).order_by('-id')

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
        'articles': articles, # ডাইনামিক আর্টিকেলগুলো কন্টেক্সটে পাস করা হলো
        'selected_uni': uni_id,
        'selected_country': country_name,
        'selected_dept': dept_name,
        'query': query,
    })
    

def professor_detail(request, pk):
    professor = get_object_or_404(Professor, pk=pk, is_verified=True)
    reviews = professor.reviews.all().order_by('-created_at')
    top_reviews = professor.reviews.filter(rating__gte=4).order_by('-rating', '-created_at')[:10]
    
    is_bookmarked = False
    has_reviewed = False 
    is_student = False 
    
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, professor=professor).exists()
        has_reviewed = Review.objects.filter(user=request.user, professor=professor).exists()
        
        if hasattr(request.user, 'student_profile'):
            is_student = True

    # --- ডাইনামিক ডেডলাইন লজিক ---
    today = date.today()
    
    deadline_info = SubjectDeadline.objects.filter(
        university=professor.university,
        name__icontains=professor.department
    ).first()

    int_status, dom_status = None, None
    display_intl_date, display_dom_date = None, None
    upcoming_semester = "Upcoming"

    def parse_date(date_val):
        if not date_val:
            return None
        if isinstance(date_val, str):
            date_str = date_val.strip()
            
            text_deadlines = ['rolling', 'tba', 'not available', 'n/a', '-', 'none', 'tbd']
            if date_str.lower() in text_deadlines:
                return 'TEXT_DEADLINE'
                
            date_formats = [
                '%Y-%m-%d', '%b %d, %Y', '%B %d, %Y', 
                '%d %b %Y', '%m/%d/%Y', '%d/%m/%Y'
            ]
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        return date_val

    if deadline_info:
        # ১. International Deadline ক্যালকুলেশন
        intl_dates = [
            ('Fall', parse_date(deadline_info.fall_intl_deadline)),
            ('Spring', parse_date(deadline_info.spring_intl_deadline)),
            ('Summer', parse_date(deadline_info.summer_intl_deadline))
        ]
        
        valid_intl = []
        has_rolling_intl = False
        for term, d in intl_dates:
            if d == 'TEXT_DEADLINE':
                has_rolling_intl = True
                upcoming_semester = term
            elif d and d >= today:
                valid_intl.append((term, d))
                
        valid_intl.sort(key=lambda x: x[1])

        if has_rolling_intl:
            int_status = {"color": "text-green-700 bg-green-100 border-green-200", "text": "Open / Rolling"}
        elif valid_intl:
            upcoming_semester = valid_intl[0][0]
            display_intl_date = valid_intl[0][1]
            days_left = (display_intl_date - today).days
            
            if days_left == 0:
                int_status = {"color": "text-orange-700 bg-orange-100 border-orange-200 animate-pulse", "text": "⚠️ Ends Today!"}
            else:
                int_status = {"color": "text-green-700 bg-green-100 border-green-200", "text": f"⏳ {days_left} days left"}
        else:
            int_status = {"color": "text-red-700 bg-red-100 border-red-200", "text": "🚫 Closed"}

        # ২. Domestic Deadline ক্যালকুলেশন
        dom_dates = [
            ('Fall', parse_date(deadline_info.fall_dom_deadline)),
            ('Spring', parse_date(deadline_info.spring_dom_deadline)),
            ('Summer', parse_date(deadline_info.summer_dom_deadline))
        ]
        
        valid_dom = []
        has_rolling_dom = False
        for term, d in dom_dates:
            if d == 'TEXT_DEADLINE':
                has_rolling_dom = True
                if not valid_intl and not has_rolling_intl:
                    upcoming_semester = term
            elif d and d >= today:
                valid_dom.append((term, d))
                
        valid_dom.sort(key=lambda x: x[1])

        if has_rolling_dom:
            dom_status = {"color": "text-green-700 bg-green-100 border-green-200", "text": "Open / Rolling"}
        elif valid_dom:
            if not valid_intl and not has_rolling_intl: 
                upcoming_semester = valid_dom[0][0]
            display_dom_date = valid_dom[0][1]
            days_left = (display_dom_date - today).days
            
            if days_left == 0:
                dom_status = {"color": "text-orange-700 bg-orange-100 border-orange-200 animate-pulse", "text": "⚠️ Ends Today!"}
            else:
                dom_status = {"color": "text-green-700 bg-green-100 border-green-200", "text": f"⏳ {days_left} days left"}
        else:
            dom_status = {"color": "text-red-700 bg-red-100 border-red-200", "text": "🚫 Closed"}

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, "দুঃখিত! শুধুমাত্র শিক্ষার্থীরাই প্রফেসরদের রিভিউ দিতে পারবেন।")
            return redirect('professor_detail', pk=pk)
            
        student = getattr(request.user, 'student_profile', None)
        if student and student.is_verified:
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
        'has_reviewed': has_reviewed,
        'is_student': is_student,
        'deadline_info': deadline_info,
        'int_status': int_status,       
        'dom_status': dom_status,
        'display_intl_date': display_intl_date, 
        'display_dom_date': display_dom_date,   
        'upcoming_semester': upcoming_semester, 
    })


def signup_view(request):
    if request.method == 'POST':
        # Cloudflare Turnstile Verification for Signup
        turnstile_response = request.POST.get('cf-turnstile-response')
        secret_key = '0x4AAAAAAEGTmzZjDVZnFP2zLadAErU4-b0' # আপনার আসল Secret Key দিন
        verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        
        response = requests.post(verify_url, data={'secret': secret_key, 'response': turnstile_response})
        result = response.json()
        
        if not result.get('success'):
            messages.error(request, 'ক্যাপচা ভেরিফিকেশন ব্যর্থ হয়েছে। দয়া করে আবার চেষ্টা করুন।')
            return render(request, 'auth/signup.html')

        # মূল সাইনআপ লজিক
        role = request.POST.get('role')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        existing_email_user = User.objects.filter(email=email).first()
        
        if existing_email_user:
            if existing_email_user.is_active:
                messages.error(request, "এই ইমেইল দিয়ে ইতিমধ্যেই একটি অ্যাক্টিভ অ্যাকাউন্ট খোলা আছে। দয়া করে লগইন করুন।")
                return redirect('signup')
            else:
                if User.objects.filter(username=username).exclude(id=existing_email_user.id).exists():
                    messages.error(request, "এই ইউজারনেমটি আগে থেকেই ব্যবহার করা হচ্ছে।")
                    return redirect('signup')
                
                existing_email_user.username = username
                existing_email_user.set_password(password)
                existing_email_user.save()
                user = existing_email_user
                
                if role == 'student' and not hasattr(user, 'student_profile'):
                    StudentProfile.objects.create(user=user)
                    
                OTPVerification.objects.filter(user=user).delete()
        else:
            if User.objects.filter(username=username).exists():
                messages.error(request, "এই ইউজারনেমটি আগে থেকেই ব্যবহার করা হচ্ছে।")
                return redirect('signup')

            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = False 
            user.save()
            
            if role == 'student':
                StudentProfile.objects.create(user=user)
                
        otp_obj = OTPVerification.objects.create(user=user)
        otp_obj.generate_otp()

        subject = 'Verify your Email - Professorkhujun'
        message = f'আপনার অ্যাকাউন্ট ভেরিফিকেশন কোড (OTP) হলো: {otp_obj.otp}'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

        request.session['verification_user_id'] = user.id
        request.session['signup_role'] = role
        
        if existing_email_user:
            messages.info(request, "আপনার অ্যাকাউন্টটি ভেরিফাই করা ছিল না। নতুন একটি ৬-ডিজিটের কোড পাঠানো হয়েছে।")
        else:
            messages.success(request, "আপনার ইমেইলে একটি ৬-ডিজিটের কোড পাঠানো হয়েছে।")
            
        return redirect('verify_otp')
            
    return render(request, 'auth/signup.html')


def verify_otp(request):
    user_id = request.session.get('verification_user_id')
    role = request.session.get('signup_role')

    if not user_id:
        return redirect('signup')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        otp_obj = OTPVerification.objects.filter(user=user).first()

        if otp_obj and otp_obj.otp == entered_otp:
            user.is_active = True
            user.save()
            otp_obj.delete()

            auth_backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user, backend=auth_backend)
            
            del request.session['verification_user_id']
            if 'signup_role' in request.session:
                del request.session['signup_role']

            messages.success(request, "আপনার ইমেইল সফলভাবে ভেরিফাই হয়েছে!")
            
            if role == 'student':
                return redirect('home')
            else:
                return redirect('professor_dashboard')
        else:
            messages.error(request, "ভুল OTP! দয়া করে সঠিক কোড দিন।")

    return render(request, 'auth/verify_otp.html')


def resend_otp(request):
    user_id = request.session.get('verification_user_id')

    if not user_id:
        messages.error(request, "সেশন শেষ হয়ে গেছে বা আপনি সঠিক পেজ থেকে আসেননি। দয়া করে আবার সাইন আপ বা লগইন করুন।")
        return redirect('signup')

    user = get_object_or_404(User, id=user_id)

    # আগের কোনো OTP থাকলে ডিলিট করে নতুন তৈরি করা
    OTPVerification.objects.filter(user=user).delete()
    otp_obj = OTPVerification.objects.create(user=user)
    otp_obj.generate_otp()

    # নতুন OTP ইমেইলে পাঠানো
    subject = 'Resend OTP - Professorkhujun'
    message = f'আপনার নতুন অ্যাকাউন্ট ভেরিফিকেশন কোড (OTP) হলো: {otp_obj.otp}'
    
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
        messages.success(request, "নতুন একটি ৬-ডিজিটের কোড আপনার ইমেইলে পাঠানো হয়েছে।")
    except Exception as e:
        messages.error(request, "ইমেইল পাঠাতে সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।")

    return redirect('verify_otp')

def login_view(request):
    if request.method == 'POST':
        # Cloudflare Turnstile Verification for Login
        turnstile_response = request.POST.get('cf-turnstile-response')
        secret_key = '0x4AAAAAAEGTmzZjDVZnFP2zLadAErU4-b0' # আপনার আসল Secret Key দিন
        verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        
        response = requests.post(verify_url, data={'secret': secret_key, 'response': turnstile_response})
        result = response.json()
        
        if not result.get('success'):
            messages.error(request, 'ক্যাপচা ভেরিফিকেশন ব্যর্থ হয়েছে। দয়া করে আবার চেষ্টা করুন।')
            return render(request, 'auth/login.html')

        # মূল লগইন লজিক
        username = request.POST.get('username')
        password  = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if user.is_superuser or user.is_staff:
                return redirect('admin:index')
            elif hasattr(user, 'student_profile'):
                return redirect('home')
            else:
                return redirect('professor_dashboard')
        else:
            messages.error(request, "ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে, অথবা আপনার অ্যাকাউন্টটি অ্যাক্টিভ নয়।")
            
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def professor_dashboard(request):
    if hasattr(request.user, 'student_profile') and not request.user.is_superuser:
        messages.error(request, "এই পেজটি শুধুমাত্র প্রফেসরদের জন্য।")
        return redirect('home')

    professor = Professor.objects.filter(user=request.user).first()
    has_pending_claim = ProfileClaimRequest.objects.filter(user=request.user, is_approved=False).exists()
    show_verified_popup = False
    show_rejected_popup = request.session.pop('is_rejected', False) 

    if professor and professor.is_verified:
        if not request.session.get('verified_popup_seen'):
            show_verified_popup = True
            request.session['verified_popup_seen'] = True

    if request.method == 'POST':
        action = request.POST.get('action') 

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
                user=request.user, 
                name=name, 
                university_id=uni_id,
                department=dept, 
                research_area=research, 
                email=email,
                image=image, 
                is_verified=False
            )
            messages.success(request, "আপনার প্রোফাইল সাবমিট করা হয়েছে! অ্যাডমিন ভেরিফাই করলে এটি সাইটে দেখা যাবে।")
            return redirect('professor_dashboard')

        elif action == 'update_request' and professor:
            changes = []
            
            def check_change(field_name, label, old_val):
                new_val = request.POST.get(field_name, '').strip()
                old_val = str(old_val).strip() if old_val else ''
                
                if new_val != old_val:
                    if new_val == '':
                        changes.append(f"📌 {label}:\n[তথ্য মুছে ফেলা হয়েছে]")
                    else:
                        changes.append(f"📌 {label}:\n{new_val}")

            check_change('designation', 'Designation', professor.designation)
            check_change('phone', 'Phone Number', professor.phone)
            check_change('website', 'Personal Website', professor.website)
            check_change('uni_website', 'University Website', professor.uni_website)
            check_change('lab_name', 'Lab Name', professor.lab_name)
            check_change('lab_description', 'Lab Description', professor.lab_description)
            check_change('bio', 'Biography', professor.bio)
            check_change('publications', 'Selected Publications', professor.publications)

            if changes:
                requested_changes_text = "\n\n".join(changes)
                ProfessorUpdateRequest.objects.create(professor=professor, requested_changes=requested_changes_text)
                messages.success(request, "আপনার আপডেট রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে।")
            else:
                messages.info(request, "আপনি কোনো নতুন তথ্য পরিবর্তন করেননি।")
                
            return redirect('professor_dashboard')

    universities = University.objects.all()
    unclaimed_professors = Professor.objects.filter(user__isnull=True, is_verified=True)
    update_requests = ProfessorUpdateRequest.objects.filter(professor=professor).order_by('-created_at') if professor else None
    
    return render(request, 'auth/professor_dashboard.html', {
        'professor': professor,
        'universities': universities,
        'unclaimed_professors': unclaimed_professors,
        'update_requests': update_requests,
        'has_pending_claim': has_pending_claim,
        'show_verified_popup': show_verified_popup,
        'show_rejected_popup': show_rejected_popup
    })

@login_required
def toggle_bookmark(request, prof_id):
    professor = get_object_or_404(Professor, id=prof_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, professor=professor)
    
    if not created:
        bookmark.delete()
        messages.info(request, "প্রোফাইলটি বুকমার্ক থেকে সরানো হয়েছে।")
    else:
        messages.success(request, "প্রোফাইলটি সফলভাবে সেভ করা হয়েছে।")
    
    return redirect('professor_detail', pk=prof_id)

@login_required
def student_dashboard(request):
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

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount', 5)) * 100 
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
                success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('home')),
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            print(f"Stripe Error: {e}") 
            messages.error(request, f"পেমেন্ট শুরু করতে সমস্যা হয়েছে: {e}") 
    return redirect('home')

def payment_success(request):
    session_id = request.GET.get('session_id')
    user_email = None
    
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            user_email = session.customer_details.email
        except Exception:
            pass

    if user_email:
        subject = 'Thank You for Supporting Professorkhujun! 💙'
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
            print(f"Email error: {e}")

    messages.success(request, "আপনার অনুদানের জন্য অসংখ্য ধন্যবাদ! আপনাকে একটি কনফার্মেশন ইমেইল পাঠানো হয়েছে।")
    return redirect('home')

def university_deadlines(request):
    query = request.GET.get('q', '')
    universities = University.objects.prefetch_related('subjects').all().order_by('name')
    
    slider_universities = University.objects.all().order_by('-id')[:5]
    
    if query:
        universities = universities.filter(
            Q(name__icontains=query) | Q(country__icontains=query)
        )
        
    return render(request, 'university_deadlines.html', {
        'universities': universities,
        'slider_universities': slider_universities, 
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

def about_view(request):
    return render(request, 'pages/about.html')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        messages.success(request, "আপনার মেসেজটি সফলভাবে পাঠানো হয়েছে। আমরা শীঘ্রই আপনার সাথে যোগাযোগ করব!")
        return redirect('contact')
        
    return render(request, 'pages/contact.html')

def privacy_policy_view(request):
    return render(request, 'pages/privacy.html')

def terms_view(request):
    return render(request, 'pages/terms.html')

def university_deadline_detail(request, pk):
    university = get_object_or_404(University, pk=pk)
    
    subjects = university.subjects.all()
    
    context = {
        'university': university,
        'phd_subjects': subjects.filter(degree_level='phd'),
        'masters_subjects': subjects.filter(degree_level='masters'),
        'bachelors_subjects': subjects.filter(degree_level='bachelors'),
    }
    return render(request, 'university_deadline_detail.html', context)


def article_list(request):
    # সবগুলো আর্টিকেল লেটেস্ট অনুযায়ী ফেচ করা হচ্ছে
    articles = Article.objects.all().order_by('-created_at')
    return render(request, 'pages/article_list.html', {'articles': articles})

def article_detail(request, pk): # id এর জায়গায় pk লিখুন
    article = get_object_or_404(Article, pk=pk) # id=id এর জায়গায় pk=pk লিখুন
    
    # সেশন চেক করার লজিকটি আগের মতোই থাকবে
    session_key = f'viewed_article_{article.pk}' # এখানেও id এর জায়গায় pk
    
    if not request.session.get(session_key, False):
        article.views += 1
        article.save()
        request.session[session_key] = True

    context = {
        'article': article
    }
    return render(request, 'pages/article_detail.html', context)