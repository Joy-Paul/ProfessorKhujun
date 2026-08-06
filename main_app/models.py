from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils.timezone import now
from django_countries.fields import CountryField
import random

# class University(models.Model):
#     name = models.CharField(max_length=200, unique=True)
#     location = models.CharField(max_length=100, blank=True, null=True)
#     country = CountryField(blank_label='(Select Country)')

#     # Fall Semester Deadlines
#     fall_intl_deadline = models.CharField(max_length=100, blank=True, null=True, help_text="Example: Dec 15, 2026 or Rolling")
#     fall_dom_deadline = models.CharField(max_length=100, blank=True, null=True)
    
#     # Spring Semester Deadlines
#     spring_intl_deadline = models.CharField(max_length=100, blank=True, null=True)
#     spring_dom_deadline = models.CharField(max_length=100, blank=True, null=True)

#     @property
#     def intl_days_left(self):
#         if self.intl_deadline_date:
#             delta = self.intl_deadline_date - now().date()
#             return delta.days
#         return None

#     @property
#     def domestic_days_left(self):
#         if self.domestic_deadline_date:
#             delta = self.domestic_deadline_date - now().date()
#             return delta.days
#         return None

#     def __str__(self): 
#         return self.name

class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    # লোগো আপলোড করার জন্য নতুন ফিল্ড:
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    country = CountryField(blank_label='(Select Country)')

    fall_intl_deadline = models.CharField(max_length=100, blank=True, null=True, help_text="Example: Dec 15, 2026 or Rolling")
    fall_dom_deadline = models.CharField(max_length=100, blank=True, null=True)
    spring_intl_deadline = models.CharField(max_length=100, blank=True, null=True)
    spring_dom_deadline = models.CharField(max_length=100, blank=True, null=True)
    # এই নতুন ফিল্ডটি যোগ করুন:
    short_name = models.CharField(max_length=20, blank=True, null=True, help_text="যেমন: MIT, LPU, ISM")

    def __str__(self): 
        return self.name

# class SubjectDeadline(models.Model):
#     DEGREE_CHOICES = [
#         ('phd', 'PhD'),
#         ('masters', 'Masters'),
#         ('bachelors', 'Bachelors'),
#         ('certificate', 'Certificate'),
#     ]
    
#     PROGRAM_CHOICES = [
#         ('on_campus', 'On-Campus'),
#         ('online', 'Online Program'),
#     ]
    
#     university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='subjects')
#     name = models.CharField(max_length=200, help_text="Example: Computer Science")
    
#     # Filters
#     degree_level = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='phd', help_text="ডিগ্রির ধরন সিলেক্ট করুন")
#     program_type = models.CharField(max_length=20, choices=PROGRAM_CHOICES, default='on_campus', help_text="প্রোগ্রামের ধরন")
    
#     # Priority Deadline
#     priority_deadline = models.CharField("Priority Deadline", max_length=100, blank=True, null=True)

#     # Fall Deadlines (Separate for Domestic & Intl)
#     fall_intl_deadline = models.CharField("Fall (International)", max_length=100, blank=True, null=True)
#     fall_dom_deadline = models.CharField("Fall (Domestic)", max_length=100, blank=True, null=True)
    
#     # Spring Deadlines
#     spring_intl_deadline = models.CharField("Spring (International)", max_length=100, blank=True, null=True)
#     spring_dom_deadline = models.CharField("Spring (Domestic)", max_length=100, blank=True, null=True)
    
#     # Summer Deadlines
#     summer_intl_deadline = models.CharField("Summer (International)", max_length=100, blank=True, null=True)
#     summer_dom_deadline = models.CharField("Summer (Domestic)", max_length=100, blank=True, null=True)

#     def __str__(self):
#         return f"{self.name} ({self.get_degree_level_display()}) - {self.university.name}"


class SubjectDeadline(models.Model):
    # 'Certificate' এখান থেকে সরিয়ে ফেলা হয়েছে
    DEGREE_CHOICES = [
        ('phd', 'PhD'),
        ('masters', 'Masters'),
        ('bachelors', 'Bachelors'),
    ]
    
    PROGRAM_CHOICES = [
        ('on_campus', 'On-Campus'),
        ('online', 'Online Program'),
    ]
    
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200, help_text="Example: Computer Science")
    
    # Filters
    degree_level = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='phd', help_text="ডিগ্রির ধরন সিলেক্ট করুন")
    program_type = models.CharField(max_length=20, choices=PROGRAM_CHOICES, default='on_campus', help_text="প্রোগ্রামের ধরন")
    is_certificate = models.BooleanField(default=False, help_text="এটি কি একটি সার্টিফিকেট কোর্স?") # নতুন ফিল্ড
    
    # Priority Deadline
    priority_deadline = models.CharField("Priority Deadline", max_length=100, blank=True, null=True)

    # Fall Deadlines (Separate for Domestic & Intl)
    fall_intl_deadline = models.CharField("Fall (International)", max_length=100, blank=True, null=True)
    fall_dom_deadline = models.CharField("Fall (Domestic)", max_length=100, blank=True, null=True)
    
    # Spring Deadlines
    spring_intl_deadline = models.CharField("Spring (International)", max_length=100, blank=True, null=True)
    spring_dom_deadline = models.CharField("Spring (Domestic)", max_length=100, blank=True, null=True)
    
    # Summer Deadlines
    summer_intl_deadline = models.CharField("Summer (International)", max_length=100, blank=True, null=True)
    summer_dom_deadline = models.CharField("Summer (Domestic)", max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_degree_level_display()}) - {self.university.name}"
    
class Professor(models.Model):
    name = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    research_area = models.TextField()
    email = models.EmailField()
    bio = models.TextField(blank=True)
    lab_link = models.URLField(blank=True)
    website = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='prof_images/', blank=True, null=True)
    designation = models.CharField(max_length=100, default="Professor") 
    phone = models.CharField(max_length=20, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    publications = models.TextField(blank=True, help_text="আপনার পাবলিকেশনগুলোর লিস্ট দিন (প্রতিটি নতুন লাইনে)")
    lab_name = models.CharField(max_length=255, blank=True, null=True)
    lab_description = models.TextField(blank=True, null=True)
    lab_image = models.ImageField(upload_to='lab_images/', blank=True, null=True)
    uni_website = models.URLField(blank=True, null=True, help_text="ইউনিভার্সিটির ওয়েবসাইটের লিংক")
    
    def __str__(self): 
        return self.name

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg is not None:
            return round(avg, 1)
        return 0.0
    @property
    def total_reviews(self):
        return self.reviews.count()

    @property
    def rating_distribution(self):
        total = self.reviews.count()
        # যদি কোনো রিভিউ না থাকে, তাহলে সব ০% দেখাবে
        if total == 0:
            return {'five': 0, 'four': 0, 'three': 0, 'two': 0, 'one': 0}
        
        counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for review in self.reviews.all():
            if review.rating in counts:
                counts[review.rating] += 1
                
        # শতাংশ (Percentage) হিসাব করা হচ্ছে
        return {
            'five': int((counts[5] / total) * 100),
            'four': int((counts[4] / total) * 100),
            'three': int((counts[3] / total) * 100),
            'two': int((counts[2] / total) * 100),
            'one': int((counts[1] / total) * 100),
        }

class Review(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    is_verified = models.BooleanField(default=False, help_text="অ্যাডমিন ভেরিফাই করলে তবেই রিভিউ দিতে পারবে")

    def __str__(self):
        return f"Student: {self.user.username}"
    
class ProfessorUpdateRequest(models.Model):
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE)
    requested_changes = models.TextField(help_text="কী পরিবর্তন করতে চান তা বিস্তারিত লিখুন")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update Request from {self.professor.name}"
    
class ProfileClaimRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} claims {self.professor.name}"

class Bookmark(models.Model):
    STATUS_CHOICES = [
        ('saved', 'To Review (দেখতে হবে)'),
        ('emailed', 'Email Sent (ইমেইল পাঠিয়েছি)'),
        ('interview', 'Interviewing (ইন্টারভিউ চলছে)'),
        ('accepted', 'Accepted (অ্যাকসেপ্টেড)'),
        ('rejected', 'Rejected (রিজেক্টেড)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='saved')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'professor')

    def __str__(self):
        return f"{self.user.username} saved {self.professor.name}"
    
class Report(models.Model):
    ISSUE_CHOICES = [
        ('wrong_email', 'ভুল ইমেইল অ্যাড্রেস'),
        ('wrong_deadline', 'ভুল ডেডলাইন'),
        ('left_uni', 'ইউনিভার্সিটি ছেড়ে দিয়েছেন'),
        ('spam', 'ফেক প্রোফাইল বা স্প্যাম'),
        ('other', 'অন্যান্য সমস্যা'),
    ]
    
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    issue_type = models.CharField(max_length=50, choices=ISSUE_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report on {self.professor.name} - {self.issue_type}"

class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp_profile')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()

# class Article(models.Model):
#     title = models.CharField(max_length=255)
#     category = models.CharField(max_length=100, help_text="Ex: Application Guide, Communication, Success Story")
#     summary = models.TextField(help_text="Short description for the card")
#     # নতুন ফিল্ড: সম্পূর্ণ আর্টিকেল লেখার জন্য
#     content = models.TextField(help_text="Full text of the article", null=True, blank=True)
#     read_time = models.IntegerField(help_text="Reading time in minutes")
#     views = models.DecimalField(max_digits=5, decimal_places=1, help_text="Ex: 1.2, 3.4 for k views")
#     author_image = models.ImageField(upload_to='article_authors/', null=True, blank=True)
    
#     # নতুন ফিল্ডটি যোগ করুন
#     background_image = models.ImageField(upload_to='article_bgs/', null=True, blank=True, help_text="Upload an image for card background (Optional)")

#     # ভিউ কাউন্টের জন্য এই ফিল্ডটি ব্যবহার করুন
#     views = models.PositiveIntegerField(default=0)
    
#     created_at = models.DateTimeField(auto_now_add=True)

#     # এই নতুন ফাংশনটি যোগ করুন
#     @property
#     def formatted_views(self):
#         if self.views >= 1000:
#             val = self.views / 1000.0
#             # যদি 1.0k হয়, তবে শুধু 1k দেখাবে, নাহলে 1.5k দেখাবে
#             return f"{val:.1f}k".replace('.0k', 'k')
#         return str(self.views)

#     def __str__(self):
#         return self.title

class Article(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, help_text="Ex: Application Guide, Communication, Success Story")
    summary = models.TextField(help_text="Short description for the card")
    content = models.TextField(help_text="Full text of the article", null=True, blank=True)
    read_time = models.IntegerField(help_text="Reading time in minutes")
    author_image = models.ImageField(upload_to='article_authors/', null=True, blank=True)
    background_image = models.ImageField(upload_to='article_bgs/', null=True, blank=True, help_text="Upload an image for card background (Optional)")

    # শুধুমাত্র একটি views ফিল্ড থাকবে
    views = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def formatted_views(self):
        if self.views >= 1000:
            val = self.views / 1000.0
            return f"{val:.1f}k".replace('.0k', 'k')
        return str(self.views)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article_detail', kwargs={'pk': self.pk})

# URL পাওয়ার জন্য (urls.py এ সেট করার পর এটি কাজে লাগবে)
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article_detail', kwargs={'pk': self.pk})