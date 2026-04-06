# models.py এর একদম উপরে এটি যোগ করবেন
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg  # গড় রেটিং হিসাব করার জন্য
from django.utils.timezone import now # এই লাইনটি একদম ওপরে ইম্পোর্ট করবেন

class University(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)

    # --- নতুন ডেডলাইন ফিল্ড ---
    domestic_deadline = models.CharField(max_length=255, blank=True, null=True, help_text="Example: Fall - Dec 15, Spring - Oct 1")
    international_deadline = models.CharField(max_length=255, blank=True, null=True, help_text="Example: Fall - Dec 1, Spring - Sep 15")
    
    # --- নতুন: কাউন্টডাউনের জন্য সঠিক তারিখ ---
    intl_deadline_date = models.DateField(blank=True, null=True, help_text="ইন্টারন্যাশনাল ডেডলাইনের সঠিক তারিখ দিন")
    domestic_deadline_date = models.DateField(blank=True, null=True, help_text="ডোমেস্টিক ডেডলাইনের সঠিক তারিখ দিন")

    # অটোমেটিক দিন হিসাব করার লজিক (International)
    @property
    def intl_days_left(self):
        if self.intl_deadline_date:
            delta = self.intl_deadline_date - now().date()
            return delta.days
        return None

    # অটোমেটিক দিন হিসাব করার লজিক (Domestic)
    @property
    def domestic_days_left(self):
        if self.domestic_deadline_date:
            delta = self.domestic_deadline_date - now().date()
            return delta.days
        return None

    def __str__(self): return self.name

class Professor(models.Model):
    name = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    research_area = models.TextField()
    email = models.EmailField()
    bio = models.TextField(blank=True) # প্রফেসরের বিস্তারিত তথ্য
    lab_link = models.URLField(blank=True)
    website = models.URLField(blank=True, null=True) # যদি আগে lab_link থাকে, তবে website করে দিন
    image = models.ImageField(upload_to='prof_images/', blank=True, null=True)
    designation = models.CharField(max_length=100, default="Professor") 
    phone = models.CharField(max_length=20, blank=True, null=True)
    # ২. প্রফেসরের সাথে ইউজার লিঙ্ক করা (যাতে তারা লগইন করতে পারে)
# আপনার আগের Professor মডেলে শুধু এই লাইনটি যোগ করুন:
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    # নতুন ফিল্ডসমূহ:
    publications = models.TextField(blank=True, help_text="আপনার পাবলিকেশনগুলোর লিস্ট দিন (প্রতিটি নতুন লাইনে)")
    lab_name = models.CharField(max_length=255, blank=True, null=True)
    lab_description = models.TextField(blank=True, null=True)
    lab_image = models.ImageField(upload_to='lab_images/', blank=True, null=True)
    uni_website = models.URLField(blank=True, null=True, help_text="ইউনিভার্সিটির ওয়েবসাইটের লিংক")
    
    def __str__(self): return self.name

    # --- রেটিং অটোমেটিক হিসাব করার লজিক ---
    @property
    def average_rating(self):
        # এই প্রফেসরের সব রিভিউ থেকে রেটিংয়ের গড় (Average) বের করবে
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg is not None:
            return round(avg, 1) # দশমিকের পর এক ঘর দেখাবে (যেমন: 4.8)
        return 0.0 # রিভিউ না থাকলে 0.0 দেখাবে

class Review(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)

# ১. স্টুডেন্ট প্রোফাইল (ভেরিফিকেশনের জন্য)
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    is_verified = models.BooleanField(default=False, help_text="অ্যাডমিন ভেরিফাই করলে তবেই রিভিউ দিতে পারবে")

    def __str__(self):
        return f"Student: {self.user.username}"
    
# ৩. প্রফেসরের ইনফরমেশন চেঞ্জ রিকোয়েস্ট
class ProfessorUpdateRequest(models.Model):
    professor = models.ForeignKey('Professor', on_delete=models.CASCADE)
    requested_changes = models.TextField(help_text="কী পরিবর্তন করতে চান তা বিস্তারিত লিখুন (যেমন: আমার ফোন নম্বর 017... করে দিন)")
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # একই ইউজার যেন একই প্রফেসরকে দুইবার বুকমার্ক না করতে পারে
        unique_together = ('user', 'professor')

    def __str__(self):
        return f"{self.user.username} saved {self.professor.name}"